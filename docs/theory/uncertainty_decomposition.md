# Epistemic vs aleatoric uncertainty

Predictive uncertainty trong regression có thể tách thành hai phần:

```text
total predictive variance = epistemic variance + aleatoric variance
```

Trong project này:

- Epistemic: phương sai giữa mean predictions của các ensemble members.
- Aleatoric: trung bình variance do từng model dự đoán từ `log_var`.

## Epistemic uncertainty

Epistemic là "mô hình chưa biết". Nó thường cao ở vùng dữ liệu:

- ít hoặc chưa có điểm labeled gần đó,
- nằm ngoài vùng train ban đầu,
- khiến các model độc lập dự đoán khác nhau.

Đây là tín hiệu chính cho active learning. Nếu thêm nhãn ở vùng epistemic cao,
mô hình có cơ hội giảm thiếu hiểu biết ở một phần không gian feature.

## Aleatoric uncertainty

Aleatoric là "dữ liệu tự nó nhiễu". Nó có thể đến từ:

- measurement noise,
- biến mục tiêu phụ thuộc vào yếu tố không có trong feature,
- dữ liệu có nhiều target hợp lý cho cùng một vùng input.

Gán thêm nhãn tại vùng aleatoric cao không chắc làm mô hình tốt hơn nhiều, vì
nhiễu không biến mất chỉ nhờ thêm nhãn.

## Công thức trong ensemble

Với `K` model:

```text
mu_bar(x) = (1 / K) * sum_k mu_k(x)
epistemic(x) = Var_k[mu_k(x)]
aleatoric(x) = (1 / K) * sum_k exp(log_var_k(x))
total(x) = epistemic(x) + aleatoric(x)
```

Trong artifact:

- `epistemic_variance`: dùng làm acquisition score.
- `aleatoric_variance`: dùng để giải thích nhiễu.
- `total_predictive_variance`: tổng của hai phần trên.

## Ý nghĩa trên site

Scatter plot dùng size theo `epistemic_variance`, vì đó là tín hiệu chọn điểm.
Panel uncertainty vẫn hiển thị `aleatoric_variance` để người đọc thấy khác biệt:
không phải mọi bất định đều đáng mua thêm nhãn.
