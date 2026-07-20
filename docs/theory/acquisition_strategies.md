# Acquisition strategies

Acquisition strategy trả lời câu hỏi: với label budget `B`, nên chọn điểm nào
từ pool để gán nhãn tiếp?

Repo hiện có ba strategy.

## RandomSampling

Random sampling chọn `B` điểm ngẫu nhiên không lặp từ pool:

```text
S ~ Uniform(D_U, size=B)
```

Đây là baseline bắt buộc. Nếu một strategy active learning không thắng được
random trong nhiều setting, tín hiệu uncertainty hoặc cách chọn batch có vấn đề.

## GreedyVariance

GreedyVariance chọn top `B` điểm có epistemic variance cao nhất:

```text
score(x) = epistemic_variance(x)
S = top_B(score)
```

Ưu điểm:

- đơn giản,
- dễ giải thích,
- trực tiếp nhắm vào vùng mô hình chưa chắc.

Nhược điểm:

- dễ chọn nhiều điểm rất gần nhau,
- batch có thể bị tập trung vào một cụm,
- label budget bị lãng phí vì các điểm trong batch cung cấp thông tin trùng
  nhau.

Đây là điểm site cần minh họa: uncertainty cao không tự đảm bảo diversity.

## KMeansVariance

KMeansVariance là core-set approximation đơn giản:

1. Lấy top `3 * B` điểm có epistemic variance cao nhất.
2. Chạy KMeans với `n_clusters = B` trên feature space của các candidate này.
3. Trong mỗi cluster, chọn điểm gần center nhất.

Viết gọn:

```text
C = top_(3B)(epistemic_variance)
clusters = KMeans(C, n_clusters=B)
S = nearest_point_to_each_cluster_center(clusters)
```

Kết quả mong muốn:

- điểm vẫn mơ hồ vì đến từ top variance candidates,
- batch phủ nhiều vùng hơn vì bị tách theo cluster,
- dễ so sánh trực quan với GreedyVariance trên PCA scatter.

## Artifact cho KMeans

Các column hỗ trợ visual:

- `is_candidate_top_variance`: điểm thuộc top `3B` variance hay không.
- `candidate_rank`: thứ hạng variance trong candidate set.
- `cluster_id`: cụm KMeans của candidate.
- `distance_to_cluster_center`: khoảng cách tới tâm cụm.
- `is_selected_this_round`: điểm cuối cùng được chọn.

Lưu ý: KMeans chạy trên feature space, không chạy trên PCA 2D. PCA chỉ để hiển
thị cho người đọc.
