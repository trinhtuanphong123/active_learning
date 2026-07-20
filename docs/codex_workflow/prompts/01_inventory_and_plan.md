# Prompt 01: Inventory and plan

Ban dang lam viec trong repo `active_learning`.

Hay doc cac file sau truoc khi lam:

- `docs/codex_workflow/project_brief.md`
- `docs/codex_workflow/target_architecture.md`
- `docs/codex_workflow/implementation_plan.md`

Nhiem vu:

1. Kiem tra trang thai repo hien tai bang `rg --files`, `git status --short`, va doc cac file Python/chinh hien co.
2. Tom tat code hien tai dang lam gi.
3. Lap ke hoach refactor chi tiet theo tung commit/phase.
4. Chua di chuyen file, chua sua code thuat toan, tru khi can tao hoac cap nhat README ngan de ghi lai huong di.

Yeu cau:

- Bao ve moi thay doi user dang co. Khong revert file da xoa/modified.
- Neu co tao README tam, phai noi ro day la dinh huong project moi.
- Final answer phai gom:
  - repo state,
  - risk,
  - proposed phase order,
  - next command/prompt nen chay.

Verification:

- `git status --short`
- Neu co sua docs/README: doc lai file vua sua.

