# Project brief: active_learning

## Muc tieu

Project nay la mot pet project de hoc va trinh bay active learning. No khong phai
mot ML production service. Gia tri chinh nam o:

1. mo hinh uncertainty,
2. thuat toan acquisition,
3. vong lap active learning,
4. artifact de chung minh qua trinh hoc,
5. mot interactive explainer giup nguoi doc hieu truc quan.

## Dinh huong mo hinh

Huong hien tai la Deep Ensembles, khong tiep tuc uu tien MC Dropout.

Ly do:

- MC Dropout la mot xap xi bien phan, cac mau dropout thuong tuong quan cao.
- Can nhieu mau inference de covariance/variance hoi tu tot.
- Deep Ensembles train nhieu neural networks doc lap voi khoi tao va shuffle khac nhau.
- Phuong sai giua cac ensemble means la epistemic uncertainty.
- Moi model du doan them `log_var` de uoc luong aleatoric uncertainty.
- Active learning chi nen dung epistemic uncertainty de chon diem.

## Bai toan demo

Dataset mac dinh: California Housing regression.

Loop:

1. Chia train/pool/test.
2. Chon mot tap labeled ban dau.
3. Train Deep Ensemble tren labeled set.
4. Du doan pool.
5. Tinh epistemic variance va aleatoric variance.
6. Acquisition strategy chon them mot batch diem.
7. Mo nhan cho cac diem da chon.
8. Lap lai va xuat artifacts.

## Chien luoc acquisition can co

- Random sampling: baseline toi thieu.
- GreedyVariance: chon top variance, de thay van de bi tap trung qua muc.
- KMeansVariance: lay top `3*M` diem variance cao, K-Means thanh `M` cum, chon diem gan tam cum nhat.

## San pham cuoi

San pham cuoi nen la mot website giai thich active learning theo tung chuong,
khong phai dashboard thuan tuy. Website doc artifacts da tao san va render visual.

Render khong duoc train, khong goi API, khong phu thuoc Torch.

