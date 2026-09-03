# G5 mutation calibration

Sample: 110 deterministic clean corpus members (procedure/trigger, 3-40 body LOC), stride-sampled from `data/corpus.jsonl`.

`new code` = an extra occurrence of an error code for the mutated member versus the pristine one under an identical `codeunit` wrapper (multiset difference) — isolates the mutation from the ambient errors a member has outside its home object.

| mutation | applicable % | any-new-error % | modal new code | expected | match |
|---|---|---|---|---|---|
| `m_delete_semicolon` | 91% | 75% | AL0111 | AL0111 | yes |
| `m_rename_call` | 91% | 55% | AL0132 | AL0132, AL0118 | yes |
| `m_rename_member` | 84% | 61% | AL0132 | AL0132 | yes |
| `m_rename_identifier` | 50% | 100% | AL0118 | AL0118 | yes |
| `m_remove_var_decl` | 50% | 100% | AL0118 | AL0118 | yes |
| `m_rename_type` | 44% | 69% | AL0185 | AL0134, AL0185, AL0118 | yes |
| `m_rename_trigger` | 6% | 0% | — | AL0162 | no |
| `m_swap_argument_count` | 86% | 30% | AL0118 | AL0126 | no |
| `m_add_parens_to_property` | 84% | 58% | AL0125 | AL0127, AL0125 | yes |
| `m_semicolon_before_else` | 11% | 92% | AL0110 | AL0110 | yes |
| `m_delete_begin` | 100% | 100% | AL0104 | AL0104, AL0109 | yes |
| `m_delete_then` | 69% | 100% | AL0104 | AL0104 | yes |
| `m_keyword_as_identifier` | 50% | 100% | AL0104 | AL0105, AL0104 | yes |
| `m_change_var_type` | 6% | 57% | AL0122 | AL0122 | yes |

## New-code histograms (per applied mutation)

- **m_delete_semicolon**: AL0111:75
- **m_rename_call**: AL0132:45, AL0118:13
- **m_rename_member**: AL0132:57, AL0118:3
- **m_rename_identifier**: AL0118:55
- **m_remove_var_decl**: AL0118:55
- **m_rename_type**: AL0185:22, AL0134:11, AL0118:6
- **m_rename_trigger**: (none)
- **m_swap_argument_count**: AL0118:20, AL0126:8
- **m_add_parens_to_property**: AL0125:36, AL0127:10, AL0135:6, AL0118:3, AL0126:2
- **m_semicolon_before_else**: AL0110:11
- **m_delete_begin**: AL0104:106, AL0414:74, AL0198:60, AL0107:50, AL0134:43, AL0121:29, AL0224:7, AL0855:5, AL0114:4, AL0297:4, AL0519:4, AL0111:4, AL0105:3, AL0197:2, AL0264:2, AL0123:2, AL0118:1, AL0110:1, AL0185:1
- **m_delete_then**: AL0104:76
- **m_keyword_as_identifier**: AL0104:52, AL0224:29, AL0414:28, AL0118:27, AL0111:22, AL0107:20, AL0198:18, AL0301:16, AL0738:15, AL0134:13, AL0519:9, AL0162:7, AL0164:6, AL0114:5, AL0197:5, AL0297:5, AL0264:3, AL0124:2, AL0139:2, AL0440:2, AL0112:2, AL0117:2, AL0105:2, AL0110:1, AL0126:1, AL0405:1, AL0192:1, AL0402:1, AL0119:1, AL0158:1
- **m_change_var_type**: AL0122:4, AL0175:3, AL0133:1
