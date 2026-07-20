# MC Dropout diagnostics

Trước khi chuyển sang Deep Ensembles, project đã kiểm tra MC Dropout theo hai
góc nhìn:

1. phân phối dự đoán tại một số điểm có gần Gaussian không,
2. covariance estimate hội tụ nhanh hay chậm khi tăng số mẫu dropout `T`.

Các kết quả dưới đây là diagnostic định hướng, không phải benchmark đầy đủ.

## Gaussian diagnostic summary

```text
Points tested: 10
Shapiro-Wilk rejected at 5%: 1
D'Agostino K^2 rejected at 5%: 0
Anderson-Darling rejected at 5%: 0
```

Per-point stats:

```text
Point 01 | pool idx  5786 | mean=-0.2576 std=0.1398 skew=+0.067 kurt=-0.282 Shapiro p=0.5602 K2 p=0.6553
Point 02 | pool idx 10871 | mean=-0.2475 std=0.1500 skew=-0.140 kurt=+0.147 Shapiro p=0.5479 K2 p=0.6049
Point 03 | pool idx  2281 | mean=-0.0754 std=0.0937 skew=-0.139 kurt=-0.486 Shapiro p=0.1442 K2 p=0.1538
Point 04 | pool idx 10451 | mean=-0.0711 std=0.1419 skew=+0.088 kurt=-0.188 Shapiro p=0.6276 K2 p=0.7819
Point 05 | pool idx  8920 | mean=+0.1381 std=0.0974 skew=-0.118 kurt=-0.008 Shapiro p=0.6296 K2 p=0.7776
Point 06 | pool idx  7772 | mean=-0.1620 std=0.1340 skew=-0.006 kurt=-0.441 Shapiro p=0.5499 K2 p=0.3112
Point 07 | pool idx   475 | mean=-0.2144 std=0.1073 skew=+0.041 kurt=+0.044 Shapiro p=0.1713 K2 p=0.9343
Point 08 | pool idx 12318 | mean=-0.1159 std=0.1261 skew=+0.363 kurt=+0.125 Shapiro p=0.03287 K2 p=0.09781
Point 09 | pool idx 11559 | mean=+0.1382 std=0.1392 skew=-0.053 kurt=-0.263 Shapiro p=0.6636 K2 p=0.7158
Point 10 | pool idx  2652 | mean=-0.2808 std=0.2417 skew=+0.119 kurt=-0.005 Shapiro p=0.7805 K2 p=0.7747
```

Diễn giải:

- Với 10 điểm kiểm tra, chỉ Shapiro-Wilk reject 1 điểm ở mức 5%.
- D'Agostino K^2 không reject điểm nào.
- Anderson-Darling không reject điểm nào.

Điều này không nói MC Dropout sai. Nó chỉ nói marginal distribution tại một số
điểm có vẻ không quá lệch Gaussian.

## Covariance convergence summary

```text
T=  10 | relative Frobenius error=1.848963 | MAE=5.508807e-04
T=  50 | relative Frobenius error=0.805355 | MAE=2.362935e-04
T= 100 | relative Frobenius error=0.553419 | MAE=1.621829e-04
T= 200 | relative Frobenius error=0.365389 | MAE=1.071985e-04
T= 500 | relative Frobenius error=0.177934 | MAE=5.270445e-05
```

Diễn giải:

- Error giảm khi tăng `T`, đúng kỳ vọng.
- Nhưng ở `T = 500`, relative Frobenius error vẫn khoảng `0.178`.
- Nếu pool có 15,000 điểm, inference cost với `T = 500` là khoảng 7.5 triệu
  forward passes cho một vòng.

Vấn đề thực dụng là tín hiệu covariance/variance hội tụ chậm so với chi phí.

## Lý do chuyển sang Deep Ensembles

MC Dropout là một xấp xỉ biến phân quanh một nghiệm đã train. Các mẫu dropout có
thể tương quan cao, nên mỗi forward pass mới không nhất thiết thêm nhiều thông
tin độc lập.

Deep Ensembles train nhiều mạng độc lập với:

- random initialization khác nhau,
- data shuffling khác nhau,
- seed khác nhau.

Với `K = 5`, inference cost trên pool 15,000 điểm là khoảng:

```text
15,000 * 5 = 75,000 forward passes
```

Con số này nhỏ hơn rất nhiều so với `T = 500` của MC Dropout. Quan trọng hơn,
variance giữa các ensemble means là tín hiệu epistemic trực tiếp và phù hợp hơn
với acquisition trong active learning.

Vì vậy hướng hiện tại của repo là:

```text
Deep Ensembles + Gaussian NLL + epistemic-only acquisition
```
