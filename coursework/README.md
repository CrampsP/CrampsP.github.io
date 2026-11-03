# Coursework

Source files from my BYU–Idaho classes, renamed so each name describes what the file does. [`docs/file-manifest.csv`](../docs/file-manifest.csv) maps every original file name to its new location.

| Folder | Course | Language / tools | Contents |
|---|---|---|---|
| [math-221d-intro-statistics](math-221d-intro-statistics/) | Math 221D: Introductory Statistics | R, Quarto | Six units: descriptive statistics, tidyverse wrangling, probability and the CLT, t-tests and ANOVA, proportions, chi-square, and regression |
| [math-325-intermediate-statistics](math-325-intermediate-statistics/) | Math 325: Intermediate Statistics | R Markdown | `analyses/`: twelve full statistical analyses. `practice/`: skill quizzes and class activities |
| [math-326-design-of-experiments](math-326-design-of-experiments/) | Math 326: Design and Analysis of Experiments | R Markdown | Experiments I designed and ran (paper airplanes, Oreo dissolving) plus factor-structure, contrast, and unbalanced-design activities |
| [ds-250-data-science-programming](ds-250-data-science-programming/) | DS 250: Data Science Programming | Python, SQL, Quarto | Client reports: baseball (SQLite) and late flights (JSON, missing data) |
| [ds-350-data-wrangling-and-visualization](ds-350-data-wrangling-and-visualization/) | DS 350: Data Wrangling and Visualization | R, tidyverse, sf, Quarto | Weekly analyses (`week-NN-topic.qmd`), study notes, and a semester project on Medicaid drug pricing |
| [machine-learning-notebooks](machine-learning-notebooks/) | Machine learning (Google Colab) | Python, scikit-learn, TensorFlow/Keras, PyTorch | Housing price regression, bike-demand neural network, traffic-sign CNN, transformer language model |
| [cse-111-python-programming](cse-111-python-programming/) | CSE 111: Programming with Functions | Python, pytest | Small programs with unit tests (chemistry formula parser, water-flow model, receipts, file I/O) |
| [ba-315-business-intelligence-power-bi](ba-315-business-intelligence-power-bi/) | BA 315: Business Intelligence | Power BI, DAX | Dashboards: cost of living, church membership statistics, temple square footage, college evaluation |
| [ai-101-102-applied-ai](ai-101-102-applied-ai/) | AI 101–102: Applied AI | Markdown | Learning roadmap, weekly notes, an essay, a lesson plan, and an agent prompt. The course's main project is [Portlight](../projects/portlight-system-monitor/) |

## Notes

- Files were renamed and moved, so some relative data paths in the code may need adjusting before you rerun it. Datasets that load from a URL work unchanged.
- Instructor-provided material is left out: course textbooks, worked examples, starter templates, and SQL textbook samples. Empty or placeholder files are also left out.
- `machine-learning-notebooks/text-generation-rnn-tensorflow-tutorial.ipynb` is my run-through of the official TensorFlow tutorial (Apache 2.0).
