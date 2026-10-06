# PMC-VQA Dataset

- [PMC-VQA Dataset](#pmc-vqa-dataset)
  - [Daraset Structure](#daraset-structure)
  - [Sample](#sample)

## Dataset Structure

**PMC-VQA** (version-1: 227k VQA pairs of 149k images).

- `train.csv`: metafile of train set
- `test.csv`: metafile of test set
- `test_clean.csv`: metafile of test clean set
- `images.zip`: images folder
- 
(**update** version-2: noncompound images).

- `train2.csv`: metafile of train set
- `test2.csv`: metafile of test set
- `images2.zip`: images folder
- 
## Sample

A row in `train.csv` is shown bellow,

| Figure_path  | PMC1064097_F1.jpg                             |
| ------------ | --------------------------------------------- |
| Question     | What is the uptake pattern in the breast?     |
| Answer       | Focal uptake pattern                          |
| Choice A     | A:Diffuse uptake pattern                      |
| Choice B     | B:Focal uptake pattern                        |
| Choice C     | C:No uptake pattern                           |
| Choice D     | D:Cannot determine from the information given |
| Answer_label | B                                             |





Explanation to each key

- Figure_path: path to the image
- Question: question corresponding to the image
- Answer: the correct answer corresponding to the image
- Choice A: the provide choice A
- Choice B: the provide choice B
- Choice C: the provide choice C
- Choice D: the provide choice D
- Anwser_label: the  correct answer label

## Dataset License
The papers used for developing PMC-VQA are from the 'Commercial Use Allowed' split of the PMC Open Access Subset. We provide the detailed PubMed Central ID for each paper and corresponding licenses in the supplementary files, which are all under CC0 or CC BY licenses. Our final dataset, PMC-VQA, is under CC BY-SA licenses so that it can be widely used to support the development of medical generative-based VQA models.
