# Hướng dẫn chạy mô hình offline và deploy site lên Render

Tài liệu này mô tả luồng end-to-end hiện tại của project:

```text
train offline trên máy -> sinh artifacts -> build JSON cho site -> push GitHub -> Render deploy static site
```

Render chỉ host website tĩnh. Render không train model, không cài Torch, không
gọi API backend.

## 1. Chuẩn bị môi trường local

Yêu cầu:

- Python 3.10+.
- Node.js 20+.
- Git.
- Trên Windows PowerShell, dùng `npm.cmd` nếu `npm.ps1` bị chặn bởi execution
  policy.

Cài dependency Python cho engine:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-train.txt
```

Cài dependency frontend:

```powershell
cd site
npm.cmd ci
cd ..
```

## 2. Chạy mô hình để tạo kết quả

### Chạy nhanh để kiểm tra pipeline

Lệnh này dùng synthetic dataset nhỏ, ít model và một vòng active learning:

```powershell
python scripts/run_suite.py --quick
```

Kết quả được ghi vào:

```text
artifacts/runs/
```

Các run debug thường gồm:

```text
quick_california_random_seed42
quick_california_greedy_variance_seed42
quick_california_kmeans_variance_seed42
quick_debug
```

### Chạy full suite

Lệnh này dùng các config California Housing:

```powershell
python scripts/run_suite.py
```

Full suite sẽ lâu hơn vì train Deep Ensemble nhiều vòng hơn. Khi chỉ muốn kiểm
tra code hoặc deploy demo, dùng `--quick` là đủ.

### Chạy từng strategy riêng

```powershell
python scripts/run_experiment.py --config configs/california_random.yaml
python scripts/run_experiment.py --config configs/california_greedy_variance.yaml
python scripts/run_experiment.py --config configs/california_kmeans_variance.yaml
```

## 3. Validate artifacts

Sau khi chạy experiment:

```powershell
python scripts/validate_artifacts.py artifacts/runs
```

Validator kiểm tra các file và cột bắt buộc theo artifact contract:

- `manifest.json`
- `metrics.csv`
- `pca_embedding.parquet`
- `selection_trace.parquet`
- `iterations/iteration_XXX.parquet`
- metadata riêng của KMeans như `cluster_id`, `candidate_rank`,
  `distance_to_cluster_center`

Nếu validator fail, không deploy site vội. Site chỉ trực quan hóa dữ liệu đã có,
nên artifact sai sẽ làm visual sai hoặc rỗng.

## 4. Build data tĩnh cho website

Parquet/CSV trong `artifacts/runs/` là source of truth nhưng không được deploy
trực tiếp. Site đọc JSON nhẹ trong `site/public/artifacts/`.

Build JSON bundle:

```powershell
python scripts/build_site_data.py
```

Mặc định script chọn một nhóm run so sánh nhất quán cho public site. Nghĩa là nếu
`artifacts/runs/` đang có cả `quick_*` và full California runs, bundle deploy sẽ
ưu tiên nhóm full California gồm Random, GreedyVariance và KMeansVariance. Cách
này tránh lỗi chart bị trộn RMSE synthetic debug với RMSE California.

Nếu bạn cần export mọi run để kiểm tra nội bộ:

```powershell
python scripts/build_site_data.py --all-runs
```

Output chính:

```text
site/public/artifacts/index.json
site/public/artifacts/runs/<run_id>/manifest.json
site/public/artifacts/runs/<run_id>/metrics.json
site/public/artifacts/runs/<run_id>/pca_embedding.json
site/public/artifacts/runs/<run_id>/selection_trace.json
site/public/artifacts/runs/<run_id>/iterations/iteration_XXX.json
```

Quan trọng:

- `artifacts/runs/` bị ignore vì có thể lớn.
- `site/public/artifacts/` là bundle đã downsample để commit và deploy.
- Muốn Render hiển thị kết quả mới, phải commit `site/public/artifacts/` sau khi
  build lại.

## 5. Kiểm tra site local

Build production:

```powershell
npm.cmd --prefix site run build
```

Chạy dev server:

```powershell
npm.cmd --prefix site run dev
```

Mở:

```text
http://127.0.0.1:5173/
```

Kiểm tra data endpoint:

```text
http://127.0.0.1:5173/artifacts/index.json
```

Nếu site mở được nhưng visual rỗng, kiểm tra:

```powershell
python scripts/build_site_data.py
```

và chắc chắn `site/public/artifacts/index.json` tồn tại.

## 6. Commit và push lên GitHub

Đúng: luồng deploy hiện tại là push code lên GitHub rồi Render lấy code từ
GitHub để build static site.

Kiểm tra status:

```powershell
git status --short
```

Các phần nên commit:

```text
al_engine/
configs/
scripts/
site/
site/public/artifacts/
docs/
tests/
requirements.txt
requirements-train.txt
render.yaml
README.md
```

Không cần commit:

```text
artifacts/runs/<run_id>/
site/dist/
site/node_modules/
.venv/
```

Các phần này đã nằm trong `.gitignore`.

Commit:

```powershell
git add .
git commit -m "Build active learning engine and static explainer site"
git push origin main
```

Nếu branch chính của bạn không phải `main`, thay `main` bằng branch thực tế.

## 7. Deploy trên Render bằng Blueprint

Repo đã có `render.yaml` ở root:

```yaml
services:
  - type: web
    name: active-learning
    runtime: static
    buildCommand: cd site && npm ci && npm run build
    staticPublishPath: site/dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

Cách deploy:

1. Push repo lên GitHub.
2. Mở Render Dashboard.
3. Chọn `New` -> `Blueprint`.
4. Connect GitHub repo chứa project.
5. Render sẽ đọc `render.yaml` ở root.
6. Review service `active-learning`.
7. Chọn `Deploy Blueprint`.
8. Chờ build xong.

Khi deploy thành công, Render cấp một URL dạng:

```text
https://<service-name>.onrender.com
```

Mỗi lần push vào branch đã connect, Render có thể auto-deploy lại site.

## 8. Deploy thủ công bằng Static Site

Nếu không dùng Blueprint, tạo Static Site thủ công:

1. Render Dashboard -> `New` -> `Static Site`.
2. Connect GitHub repo.
3. Chọn branch cần deploy.
4. Build command:

   ```text
   cd site && npm ci && npm run build
   ```

5. Publish directory:

   ```text
   site/dist
   ```

6. Không cần environment variables.
7. Create Static Site.

Nếu Render hỏi root directory, để root là repo root. Build command đã tự `cd`
vào `site`.

## 9. Sau khi deploy

Kiểm tra:

```text
https://<service>.onrender.com/
https://<service>.onrender.com/artifacts/index.json
```

Nếu `/artifacts/index.json` trả 404:

- Chưa commit `site/public/artifacts/`.
- Chưa chạy `python scripts/build_site_data.py`.
- Build đang chạy từ branch cũ.

Nếu site build fail:

- Kiểm tra log Render.
- Chạy local trước:

  ```powershell
  npm.cmd --prefix site run build
  ```

- Nếu local pass nhưng Render fail, kiểm tra `package-lock.json` đã commit chưa.

Nếu visual không đổi sau khi chạy model mới:

1. Chạy lại experiment local.
2. Chạy `python scripts/build_site_data.py`.
3. Commit thay đổi trong `site/public/artifacts/`.
4. Push lên GitHub.
5. Chờ Render redeploy.

## 10. Checklist trước khi push/deploy

```powershell
python -B -m compileall al_engine scripts tests
python -B -m unittest discover -s tests
python scripts/run_suite.py --quick
python scripts/validate_artifacts.py artifacts/runs
python scripts/build_site_data.py
npm.cmd --prefix site run build
```

Checklist kết quả:

- Tests pass.
- Artifact validator pass.
- `site/public/artifacts/index.json` tồn tại.
- `npm run build` pass.
- Không commit `artifacts/runs/`, `site/dist/`, `site/node_modules/`.

## 11. Luồng cập nhật kết quả trực quan

Khi muốn đổi dữ liệu minh họa trên website:

```powershell
python scripts/run_suite.py --quick
python scripts/validate_artifacts.py artifacts/runs
python scripts/build_site_data.py
npm.cmd --prefix site run build
git add site/public/artifacts
git commit -m "Update active learning demo artifacts"
git push origin main
```

Render sẽ build lại static site từ GitHub. Không cần chạy model trên Render.

## 12. Tham khảo Render chính thức

- Static Sites: https://render.com/docs/static-sites
- Blueprints / Infrastructure as Code: https://render.com/docs/infrastructure-as-code
- Blueprint YAML reference: https://render.com/docs/blueprint-spec
