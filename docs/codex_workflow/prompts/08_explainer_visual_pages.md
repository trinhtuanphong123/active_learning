# Prompt 08: Explainer visual pages

Ban dang lam viec trong repo `active_learning`.

Hay doc:

- `docs/codex_workflow/explainer_site_brief.md`
- `docs/codex_workflow/artifact_contract.md`

Nhiem vu:

Xay cac visual chinh cho interactive explainer.

Can implement:

1. PCA scatter plot:
   - pool points,
   - labeled points,
   - selected this round,
   - color/size theo uncertainty.
2. Iteration slider:
   - chuyen iteration thay doi scatter va metrics.
3. Strategy comparison:
   - Greedy vs KMeans tren cung PCA.
4. RMSE chart:
   - test RMSE theo iteration/num labels.
5. Uncertainty panel:
   - epistemic vs aleatoric,
   - noi ro active learning chi dung epistemic.
6. KMeans explanation:
   - top variance candidates,
   - clusters,
   - selected point gan center.

Yeu cau UX:

- Text ngan, visual la trung tam.
- Dung chapter flow, khong bien thanh admin dashboard.
- Responsive desktop/mobile co ban.
- Khong de site crash neu artifacts chua co, hien empty state huong dan build data.

Verification:

- `npm run build`
- Chay local preview/dev server.
- Kiem tra voi artifacts debug.

Final answer:

- Liet ke visuals da co.
- Noi artifact fields dang dung.
- Noi prompt tiep theo la `09_math_docs_and_narrative.md`.

