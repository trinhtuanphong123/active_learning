# Prompt 07: Explainer site scaffold

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/explainer_site_brief.md`
- `docs/codex_workflow/project_brief.md`

Nhiem vu:

Tao scaffold cho website explainer. Uu tien Vite + React neu hop ly cho repo.

Can co:

```text
site/
  package.json
  index.html
  src/
    main.jsx hoac main.tsx
    App.jsx hoac App.tsx
    data/
    components/
    scenes/
    pages/
```

Yeu cau:

1. Site doc `site/public/artifacts/index.json`.
2. Render first screen giai thich active learning bang visual, khong phai dashboard blank.
3. Co chapter navigation:
   - Overview,
   - Dataset,
   - Deep Ensemble,
   - Uncertainty,
   - Acquisition,
   - Loop,
   - Results,
   - Notes.
4. Chua can lam tat ca visuals phuc tap, nhung layout phai san sang.
5. Khong import Torch, khong goi API.

Render:

- Cap nhat `render.yaml` de build site tinh hoac serve site theo tool da chon.
- Tach `requirements-train.txt` va `requirements-site.txt` neu con Streamlit tam thoi.

Verification:

- `npm install` neu can.
- `npm run build`
- Neu co dev server, start local va kiem tra HTTP 200.

Final answer:

- Noi cong nghe site da chon va ly do.
- Noi command local dev/build.
- Noi prompt tiep theo la `08_explainer_visual_pages.md`.

