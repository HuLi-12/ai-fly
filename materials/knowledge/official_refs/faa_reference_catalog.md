# FAA 官方维修参考目录

本目录用于把翼修通当前归档的公开官方资料统一登记到资料中心，方便维修、工艺、质量三个场景直接引用。

## 已归档原始 PDF

- `official_refs/raw/faa_amt_general_handbook.pdf`
- `official_refs/raw/faa_powerplant_ch10_engine_maintenance.pdf`
- `official_refs/raw/faa_ac_43_13_1b_change_1.pdf`

## 对应解读文档

1. [FAA 航空维修技术员通用手册解读](https://www.faa.gov/regulations_policies/handbooks_manuals/aviation/amtg_handbook.pdf)
2. [FAA 发动机维护章节解读](https://www.faa.gov/regulationspolicies/handbooksmanuals/aviation/faa-h-8083-32b-chapter-10-engine-maintenance)
3. [AC 43.13-1B 维修与检查规范解读](https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_43.13-1B_CHG_1_Ed_Upd_FAA.pdf)
4. [翼修通航空维修故障排查知识卡](https://www.faa.gov/regulations_policies/handbooks_manuals/aviation/amtg_handbook.pdf)

## 建议在翼修通中的使用方式

- 智能排故：优先检索故障现象、检查顺序、停机条件、复测要求。
- 工艺偏差：检索维护记录、放行条件、标准工艺边界、返工前复核点。
- 质量处置：检索缺陷分类、隔离要求、复检要求、记录闭环内容。

## 资料治理建议

- 原始 PDF 只做归档与引用，不直接把整本手册塞进模型输出。
- Web 端优先展示中文摘要、关键检查项、适用场景和原始来源链接。
- 如果后续增加 PDF 在线预览，再把原始 PDF 通过单独接口挂到资料中心。
