# Active learning loop

Active learning là cách huấn luyện khi nhãn dữ liệu đắt. Thay vì gán nhãn toàn
bộ dataset ngay từ đầu, ta bắt đầu với một tập nhỏ đã có nhãn, rồi để mô hình đề
xuất những điểm nên gán nhãn tiếp theo.

Trong project này, bài toán demo là regression:

- `D_L`: tập đã có nhãn, dùng để train.
- `D_U`: pool chưa có nhãn, dùng để chọn điểm tiếp theo.
- `D_test`: tập test cố định, dùng để đo RMSE/MAE.
- `B`: batch size, số điểm được chọn thêm ở mỗi vòng.

Vòng lặp đang được dùng:

1. Chia dữ liệu thành train/pool và test.
2. Chọn `initial_train_size` điểm ban đầu làm `D_L`.
3. Train Deep Ensemble trên `D_L`.
4. Dự đoán toàn bộ pool `D_U`.
5. Tính epistemic uncertainty và aleatoric uncertainty.
6. Acquisition strategy chọn `B` điểm từ pool.
7. "Mở nhãn" cho các điểm được chọn, đưa vào `D_L`.
8. Lặp lại và ghi artifact cho site.

Viết gọn:

```text
train model on D_L
score each x in D_U
S = arg top/acquire B points from D_U
D_L = D_L union S
D_U = D_U \ S
```

## Vì sao label budget quan trọng

Nếu nhãn rẻ, random sampling đủ tốt: lấy thật nhiều dữ liệu rồi train. Active
learning có ý nghĩa khi mỗi nhãn tốn tiền, thời gian, chuyên gia, hoặc thí
nghiệm vật lý.

Mục tiêu không phải chọn điểm "khó" nhất bằng mọi giá. Mục tiêu là chọn điểm có
giá trị học cao nhất trên mỗi đơn vị label budget. Một batch tốt thường cần hai
yếu tố:

- Uncertainty: mô hình chưa biết rõ ở vùng đó.
- Diversity: batch không bị dồn vào cùng một vùng dữ liệu.

Đây là lý do project so sánh `GreedyVariance` với `KMeansVariance`. Greedy chỉ
nhìn uncertainty, còn KMeans thêm ràng buộc đại diện vùng dữ liệu.

## Artifact liên quan

Runner offline ghi các file trong `artifacts/runs/<run_id>/`. Site chỉ đọc bản
JSON đã build trong `site/public/artifacts/`.

Các file quan trọng:

- `metrics.csv`: RMSE/MAE và uncertainty theo iteration.
- `pca_embedding.parquet`: tọa độ PCA cố định của train/pool universe.
- `iterations/iteration_XXX.parquet`: trạng thái pool tại từng vòng.
- `selection_trace.parquet`: các điểm được chọn qua toàn bộ experiment.
