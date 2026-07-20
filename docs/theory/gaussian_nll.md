# Gaussian output và Gaussian NLL

`GaussianMLP` không chỉ dự đoán một số duy nhất. Với mỗi input `x`, model xuất
ra hai giá trị:

```text
mu(x), log_var(x)
```

Trong đó:

- `mu(x)`: dự đoán trung bình của target.
- `log_var(x)`: log của phương sai nhiễu dữ liệu.

Dùng `log_var` thay vì variance trực tiếp giúp model xuất ra số thực không bị
ràng buộc, rồi chuyển về variance dương bằng:

```text
sigma^2(x) = exp(log_var(x))
```

## Gaussian Negative Log Likelihood

Nếu giả sử target quanh `mu(x)` theo phân phối Gaussian:

```text
y | x ~ Normal(mu(x), sigma^2(x))
```

Loss âm log likelihood cho một điểm là:

```text
NLL = 0.5 * [log_var + exp(-log_var) * (y - mu)^2]
```

Code hiện tại bỏ hằng số `0.5 * log(2*pi)` vì hằng số này không ảnh hưởng tới
gradient tối ưu.

Trong `GaussianMLP._gaussian_nll`, repo clamp `log_var` vào khoảng:

```text
[-10, 10]
```

Mục đích là tránh overflow/underflow khi tính `exp(log_var)` hoặc
`exp(-log_var)`.

## Khác gì MSE

MSE chỉ học mean:

```text
loss = (y - mu)^2
```

Gaussian NLL học cả mean và mức nhiễu:

- Nếu sai số lớn nhưng model dự đoán variance quá nhỏ, loss bị phạt mạnh.
- Nếu model tăng variance quá cao ở mọi nơi, term `log_var` cũng phạt lại.

Vì vậy model có động lực học vùng nào dữ liệu nhiễu hơn. Phần này được dùng làm
`aleatoric_variance`, không dùng trực tiếp để chọn acquisition.
