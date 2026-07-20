# Deep Ensembles

Deep Ensemble dùng `K` neural networks độc lập để ước lượng dự đoán và độ bất
định. Trong repo này, `DeepEnsembleManager` train `K` bản `GaussianMLP` với seed
khác nhau:

```text
theta_1, theta_2, ..., theta_K
```

Mỗi model nhận cùng input `x` và xuất ra:

```text
mu_k(x), log_var_k(x)
```

Trong đó:

- `mu_k(x)`: mean prediction của model thứ `k`.
- `log_var_k(x)`: log variance mà model dự đoán cho nhiễu dữ liệu.

## Predictive mean

Dự đoán cuối cùng là trung bình của các mean:

```text
mu_bar(x) = (1 / K) * sum_k mu_k(x)
```

Trong code hiện tại:

```text
stacked_means.mean(axis=0)
```

## Epistemic uncertainty

Epistemic uncertainty là phần bất định do thiếu dữ liệu. Với ensemble, nó được
ước lượng bằng phương sai giữa các mean:

```text
Var_epistemic(x) = Var_k[mu_k(x)]
```

Nếu các model độc lập không đồng ý với nhau tại một điểm, nghĩa là vùng đó còn
thiếu thông tin học được từ dữ liệu đã gán nhãn.

Trong code hiện tại, phương sai này được tính bằng:

```text
stacked_means.var(axis=0)
```

Lưu ý: `numpy.var` mặc định dùng population variance (`ddof=0`). Với mục tiêu
ranking acquisition, điều này ổn vì ta cần so sánh tương đối giữa các điểm pool.

## Aleatoric uncertainty

Aleatoric uncertainty là nhiễu vốn có của dữ liệu. Mỗi model dự đoán một
variance riêng:

```text
sigma_k^2(x) = exp(log_var_k(x))
```

Ensemble lấy trung bình:

```text
Var_aleatoric(x) = (1 / K) * sum_k sigma_k^2(x)
```

Active learning trong project này chỉ dùng `Var_epistemic` để chọn điểm. Lý do:
điểm có aleatoric cao có thể vẫn nhiễu ngay cả khi gán thêm nhãn, nên không nên
đốt label budget vào đó nếu mục tiêu là giảm thiếu hiểu biết của mô hình.

## Vì sao dùng ensemble

MC Dropout tạo nhiều mẫu bằng cách bật dropout khi inference. Các mẫu đó thường
vẫn xoay quanh một nghiệm đã train. Deep Ensembles train nhiều nghiệm độc lập
hơn, nên disagreement giữa các model thường là tín hiệu epistemic mạnh hơn với
số forward pass nhỏ hơn.
