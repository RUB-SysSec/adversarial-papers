#  No more Reviewer #2: Subverting Automatic Paper-Reviewer Assignment using Adversarial Learning

This is the code repository accompaning our USENIX Security '23 paper [ No more Reviewer #2: Subverting Automatic Paper-Reviewer Assignment using Adversarial Learning](https://eisenhofer.me/data/eisenhofer-23-subverting.pdf).

> The number of papers submitted to academic conferences is steadily rising in many scientific disciplines. To handle this growth, systems for automatic *paper-reviewer assignments* are increasingly used during the reviewing process. These systems use statistical topic models to characterize the content of submissions and automate the assignment to reviewers. In this paper, we show that this automation can be manipulated using adversarial learning. We propose an attack that adapts a given paper so that it misleads the assignment and selects its own reviewers. Our attack is based on a novel optimization strategy that alternates between the feature space and problem space to realize unobtrusive changes to the paper. To evaluate the feasibility of our attack, we simulate the paper-reviewer assignment of an actual security conference (IEEE S&P) with 165 reviewers on the program committee. Our results show that we can successfully select and remove reviewers without access to the assignment system. Moreover, we demonstrate that the manipulated papers remain plausible and are often indistinguishable from benign submissions. 

## Installation

For ease of use, we include a Dockerfile with all necessary tools to reproduce the results from the paper. It can be build via

```
git clone https://github.com/RUB-SysSec/adversarial-papers.git adversarial-papers
cd adversarial-papers; ./docker.sh build
```

After building the container, it is possible to spawn a shell with
```
./docker.sh shell
```

All containers are automatically removed after the shell exits (cf. the `--rm` flag from `docker run`). To make the evaluation results both easily accessible and persistent, we map subdirectories of the evaluation folder `evaluation` from the host inside the container. To setup all paths correctly, it is therefore necessary to invoke the `docker.sh` in the base directory of the project.

## Quickstart

After building the docker container, you can test your setup by running the following command

```
./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/test.json --format_level --workers 1 --trial_name basic-test"
```

This will start the attack for the target described in `/evaluation/targets/test.json`. If everything is working properly, the attack should run for one iteration and immediately return successful. Results are stored in `evaluation/trials/basic-test`.

The main entry point for the attack is in the `src/attack.py` file. There are options provided to configure almost every aspect of the attack grouped into general, feature-space and problem-space specific configurations. When setting the number of workers to 1, the attack produces verbose output for debugging. For larger numbers, this output is *not* send to `stdout` but stored only as a log file in the respective result directory.

<details>
<summary>Commandline Interface</summary>

```
usage: attack.py [-h] [--trial_name TRIAL_NAME] [--trials_dir TRIALS_DIR] [--submissions_dir SUBMISSIONS_DIR] [--models_dir MODELS_DIR] [--workers WORKERS] [--targets_file TARGETS_FILE]
                 [--stop_condition STOP_CONDITION] [--hold_out_surrogates HOLD_OUT_SURROGATES [HOLD_OUT_SURROGATES ...]] [--max_itr MAX_ITR] [--delta DELTA] [--beam_width BEAM_WIDTH] [--step STEP]
                 [--no_successors NO_SUCCESSORS] [--reviewer_window REVIEWER_WINDOW] [--reviewer_offset REVIEWER_OFFSET] [--strategy STRATEGY] [--lambda LAMBDA] [--omega OMEGA] [--max_man_norm MAX_MAN_NORM]
                 [--max_inf_norm MAX_INF_NORM] [--only_feature_space] [--finish_all] [--no_clusters NO_CLUSTERS] [--all_topics] [--regular_beam_search] [--morphing]
                 [--morphing_reviewer_to_papers MORPHING_REVIEWER_TO_PAPERS] [--morphing_corpus_dir MORPHING_CORPUS_DIR] [--bibtexfiles BIBTEXFILES] [--synonym_model SYNONYM_MODEL]
                 [--stemming_map STEMMING_MAP] [--lang_model_path LANG_MODEL_PATH] [--lang_model_key LANG_MODEL_KEY] [--debug_coloring] [--verbose] [--text_level] [--encoding_level] [--format_level]
                 [--problem_space_finish_all] [--feature_problem_switch FEATURE_PROBLEM_SWITCH] [--problem_space_block_features] [--attack_budget ATTACK_BUDGET] [--repeat REPEAT]

optional arguments:
  -h, --help            show this help message and exit
  --trial_name TRIAL_NAME
                        Name of the trial
  --trials_dir TRIALS_DIR
                        Base dir for storing results
  --submissions_dir SUBMISSIONS_DIR
                        Base dir for target submissions
  --models_dir MODELS_DIR
                        Base dir for models
  --workers WORKERS     Number of parallel instances. Each worker utilize one CPU.
  --targets_file TARGETS_FILE
                        Path to the target file

featurespace_config:
  Parameters for Feature Space Attack

  --stop_condition STOP_CONDITION
                        Stop condition for surrogate experiments. One of ["all_successful", "one_successful", "majority_vote", "victim", "hold_out_surrogates"]
  --hold_out_surrogates HOLD_OUT_SURROGATES [HOLD_OUT_SURROGATES ...]
                        Used when stop_condition is "hold_out_surrogates"
  --max_itr MAX_ITR     Max number of iterations
  --delta DELTA         Distance between target reviewers and remaining reviewers.
  --beam_width BEAM_WIDTH
                        No of parallel candidates
  --step STEP           No of words added in each iteration
  --no_successors NO_SUCCESSORS
                        Max number of successors
  --reviewer_window REVIEWER_WINDOW
                        Size of the reviewer window
  --reviewer_offset REVIEWER_OFFSET
                        Offset of the reviewer window
  --strategy STRATEGY   Strategy for adding/removing words. One of ["basic","aggregated","topic_based","word_based"]
  --lambda LAMBDA       Hyperparameter for predictive words strategy
  --omega OMEGA         Hyperparameter for predictive words strategy
  --max_man_norm MAX_MAN_NORM
                        Limits the maximum number of modified words
  --max_inf_norm MAX_INF_NORM
                        Limits the maximum number on how often a single word can be added or removed
  --only_feature_space  Only perform feature-space attack
  --finish_all          Continue until all beam candidates are finished
  --no_clusters NO_CLUSTERS
                        Cluster similar candidates
  --all_topics          Consider all topics during candidate generation
  --regular_beam_search
                        Flag to use a regular instead of stochastic beam search
  --morphing            Flag to enable the morphing baseline
  --morphing_reviewer_to_papers MORPHING_REVIEWER_TO_PAPERS
                        Path to reviewer-paper mapping
  --morphing_corpus_dir MORPHING_CORPUS_DIR
                        Path to document corpus

problemspace_config:
  Parameters for Problem Space Attack

  --bibtexfiles BIBTEXFILES
  --synonym_model SYNONYM_MODEL
                        Path to synonym model
  --stemming_map STEMMING_MAP
                        Path to directory that contains the stemming maps
  --lang_model_path LANG_MODEL_PATH
                        Path to directory that contains the lang model (if self-finetuned model is used)
  --lang_model_key LANG_MODEL_KEY
                        Lang-Model key (if self-finetuned model is used)
  --debug_coloring
  --verbose
  --text_level
  --encoding_level
  --format_level
  --problem_space_finish_all
                        Attack tries multiple targets from feature space
  --feature_problem_switch FEATURE_PROBLEM_SWITCH
                        How often do we switch between feature and problem space
  --problem_space_block_features
                        Problem-space strategy selects features that are blocked in feature-space
  --attack_budget ATTACK_BUDGET
                        Scalar for attack budget
  --repeat REPEAT       Number of repetitions if attack fails
```
</details>

## Experiments

The full evaluation consists of ten experiments, which requires about 6.5 CPU years to fully execute. In the following, we first descirbe a subset of experiments we think are necessary to reproduce the major claims in the paper. Subsequently, we give a complete description of all ten experiments.

Each experiment is configured with a file describing all considered targets (`--targets_file`). These files are located at `evaluation/targets`. The scripts to re-generate these files are located at `scripts/targets`. Each target is optimized to run on a single-core and the experiments are therefore highly amneable for parallelization across CPU cores and machines. Note, that depending on the experiments more or less computer memory might be required (e.g., the black-box experiments require more memory per instance to store the surrogate models). Depending on the machine, this might limit the number of parallel executions. To get a good estimate, we will additionally report an approximated (!) maximal memory per instance (e.g., with 100 workers the experiment requires 100x the amount of this value). 

Finally, for almost any experiment, it is possible to continuously check the current results which might allow to stop experiments early if the numbers have sufficiently converged (see the expected results for each experiment). Sending the interrupt signal (w/ CTRL+C) should usually stop all processes, but sometimes a bit more persuasion is necessary. In this case, stopping the container proved to be an effective strategy (i.e., `docker kill <container-id>` with the container id either being autocomplete with pressing TAB or using `docker ps`).

## Main Experiments

<details>
<summary>Data</summary>

*@Artifact evaluators:* Refer to the artifact appendix for access to these files.

The main experiments require the following files
```
evaluation
├── models
│   ├── overlap_0.70
│   ├── victim
├── problemspace
│   ├── bibsources
│   ├── llms
│   └── synonyms
├── submissions
│   ├── oakland_22
├── targets
    ├── budget-vs-transformer.json
    ├── featurespace-search.json
    └── surrogates
        └── surrogate_targets_4.json
```

Pre-trained models are available at `https://zenodo.org/record/8047495`. Due to licensing issues, we can not make the target submissions publicly available. We do, however, publish all of our crawling scripts (cf. `scripts/crawler`).
</details>

<details>
<summary>(E1) Feature-space search [800 CPU hours + 31GB disk]</summary>

We start our evaluation by examining the feature-space search of our attack. For this experiment, we consider format-level transformations that can realize arbitrary changes. Other transformations are evaluated as part of experiment (E2).

The experiment can be executed with:
```
WORKERS=100
./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/
targets/featurespace-search.json --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name featurespace-search"
```

Per worker, roughly 850MB of memory are expected. Adjust the number of parallel executions accordingly. Raw results are stored in `evaluation/trials/featurespace-search` and can be analyzed with

```
./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/00_featurespace_search.py"
```

Expected output (cf. Table 2 and inline in text)
```
FEATURE-SPACE SEARCH
[+] Overall success rate
    -> 99.67%

[+] Overall run-time
    -> median: 7m 12s

[+] Overall L1
    -> min   : 9
    -> max   : 22621

[+] Ratio between modifications and original content
    -> selection: 9.42%
    -> rejection: 13.37%

[+] Modifications per objective
        Selection Rejection Substitution
    L1         704      1032         2059
    Linf        17        43           62
```
</details>

<details>
<summary>(E2) All transformations [1200 CPU hours + 32GB disk]</summary>

In experiment (E1), we have focused on format-level transformations to realize manipulations. These transformations exploit intrinsics of the submission format, which effectively allows us to make arbitrary changes to a PDF file. In experiment (E2) we consider different classes of transformations as introduced in Section 3.2.

The experiment can be executed with:
```
WORKERS=100
./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/budget-vs-transformer.json --problem_space_block_features --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --workers ${WORKERS} --trial_name budget-vs-transformer-1"
```

Per worker, roughly 2300MB of memory are expected. Adjust the number of parallel executions accordingly. Raw results are stored in `evaluation/trials/budget-vs-transformer` and can be analyzed with
```
./docker.sh run "python3 /root/adversarial-papers/
evaluation/scripts/04_all_transformations.py"
```

Expected output (cf. left part of Figure 4)
```
[+] Switches
    found no trials

[+] Budget
                   0.25   0.50   1.00   2.00   4.00
    Text      :   22.00  28.00  40.00  52.00  68.00
    + Encoding:   24.00  31.00  45.00  53.00  69.00
    + Format  :  100.00 100.00 100.00 100.00  99.00

[+] Saved plot @ evaluation/plots/all-transformations.pdf
```

Note that the full plot in Figure 4 aggregates eight of such runs. 
</details>

<details>
<summary>(E3) Surrogates [1000 CPU hours + 46GB disk]</summary>

In practice, an attacker typically does not have unrestricted access to the target system. We therefore also assume a black-box scenario and consider an adversary with only limited knowledge.

The experiment can be executed with:
```
WORKERS=50
./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/surrogates/surrogate_targets_4.json --reviewer_window 2 --delta -0.16 --reviewer_offset 1 --no_successors 128 --beam_width 4 --step 256 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name surrogates-4"
```
        
Per worker, roughly 2000MB of memory are expected. Adjust the number of parallel executions accordingly. Raw results are stored in `evaluation/trials/surrogates-4` and can be analyzed with
```
./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/05_surrogates.py"
```

Expected output (cf. Figure 5 with ensemble size 4)
```
[+] Saved plot @ evaluation/plots/surrogates.pdf
```
</details>


## All experiments

<details>
<summary>Data</summary>

The full evaluation requires the following files
```
evaluation
├── corpus
│   ├── committees_base.json
│   ├── oakland_22_large
├── models
│   ├── committees
│   ├── overlap_0.00
│   ├── overlap_0.30
│   ├── overlap_0.70
│   ├── overlap_1.00
│   ├── usenix_20
│   ├── victim
│   └── test
├── problemspace
│   ├── bibsources
│   ├── llms
│   └── synonyms
├── submissions
│   ├── test
│   ├── oakland_22
│   └── usenix_20
└── targets
    ├── budget-vs-transformer.json
    ├── committees.json
    ├── featurespace-search.json
    ├── featurespace-search-selection.json
    ├── generalization_of_attack.json
    ├── load_balancing.json
    ├── overlap.json
    ├── scaling_of_target_reviewer.json
    ├── surrogates
    │   ├── surrogate_targets_1.json
    │   ├── surrogate_targets_2.json
    │   ├── surrogate_targets_3.json
    │   ├── surrogate_targets_4.json
    │   ├── surrogate_targets_5.json
    │   ├── surrogate_targets_6.json
    │   ├── surrogate_targets_7.json
    │   └── surrogate_targets_8.json
    ├── switches-vs-transformer.json
    ├── test.json
    └── transferability.json
```

Refer to the `prerequisites` for each experiment to see which files are required.

Pre-trained models are available at `https://zenodo.org/record/8047495`. Due to licensing issues, we can not make the datatsets and target submissions publicly available. We do, however, publish all of our crawling scripts (cf. `scripts/crawler`).

</details>
<details>
<summary>00 Feature-space search</summary>

We start our evaluation by examining the feature-space search of our attack in detail. For this experiment, we consider format-level transformations that can realize arbitrary changes. Other transformations are evaluated later when we investigate the problem-space side of our attack.

The experiment can be executed with:

```
WORKERS=100

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/featurespace-search.json --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name featurespace-search"
```

Raw results are saved @ `evaluation/trials/featurespace-search`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| #Targets |  CPU  | Disc Space | Memory (per target) |
|-----:|:-----:|:----------:|:-------------------:|
|   2400   | ~800h |    31 GB   |        850MB        |

**Prerequisites**
- Targets `evaluation/targets/featurespace-search.json`
- Models `evaluation/models/victim`

**Expected results**

1. Table 2 and results inline in text    

    ```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/00_featurespace_search.py"```    

        FEATURE-SPACE SEARCH
        [+] Overall success rate
            -> 99.67%

        [+] Overall run-time
            -> median: 7m 12s

        [+] Overall L1
            -> min   : 9
            -> max   : 22621

        [+] Ratio between modifications and original content
            -> selection: 9.42%
            -> rejection: 13.37%

        [+] Modifications per objective
                Selection Rejection Substitution
            L1         704      1032         2059
            Linf        17        43           62
        

2. Appendix C    
    
    ```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/00_featurespace_search_appendix.py"```

        [+] Saved plot @ evaluation/plots/featurespace_search.pdf

</details>
<details>
<summary>01 Baseline experiments</summary>

We examine two baselines. A hill climbing approach that directly manipulates the topic vector of a submission (`topic_baseline`) and an approach that morphs a target submission with papers that already contains the correct topic-word distribution (`morphing_baseline`). 

The experiments can be executed with:

```
WORKERS=100

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/featurespace-search.json --problem_space_block_features --beam_width 1 --regular_beam_search --problem_space_block_features --feature_problem_switch 8 --step 64 --workers ${WORKERS} --format_level --strategy topic_based --trial_name topic_baseline"
```

and

```
WORKERS=100

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/featurespace-search-selection.json --problem_space_block_features --problem_space_block_features --feature_problem_switch 8 --step 64 --workers ${WORKERS} --format_level --morphing --trial_name morphing_baseline"

```

Raw results are saved @ `evaluation/trials/topic_baseline` and `evaluation/trials/morphing_baseline`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| Baseline      | #Targets |   CPU  | Disc Space | Memory (per target) |
|---------------|:--------:|:------:|:----------:|:-------------------:|
| Hill climbing |   2400   | ~1800h |    47 GB   |        ~750MB       |
| Morphing      |    800   |  ~100h |    19 GB   |        ~700MB       |

**Prerequisites**
- Targets 
  * `evaluation/targets/featurespace-search.json` 
  * `evaluation/targets/featurespace-search-selection.json`
- Corpus `evaluation/corpus/oakland_22_large`
- Models `evaluation/models/victim`

**Expected results**

Table 2 and results inline in text    

```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/01_baselines.py"```    

```
TOPIC_BASELINE
[+] Success rate: 92.20
[+] L1 (max)    : 79006
[+] Table
     Selection Rejection Substitution
L1        1652      2255         5526
Linf        38        44           98

MORPHING_BASELINE
[+] Success rate: 91.10
[+] L1 (max)    : 29291
[+] Table
     Selection Rejection Substitution
L1        3059       nan          nan
Linf        45       nan          nan
```
</details>
<details>
<summary>02 Generalization of attack</summary>

To investigate the generalization of our attack, we repeat this experiment for a second real conference. In particular, we simulate the assignment of the *29th USENIX Security Symposium* with 120 reviewers.

The experiment can be executed with:

```
WORKERS=100

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/generalization_of_attack.json --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name generalization-of-attack"
```

Raw results are saved @ `evaluation/trials/generalization-of-attack`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| #Targets |  CPU  | Disc Space | Memory (per target) |
|:--------:|:-----:|:----------:|:-------------------:|
|   2400   | ~600h |    12 GB   |        750MB        |

**Prerequisites**
- Results from feature-space search `evaluation/trials/featurespace-search`
- Targets `evaluation/targets/generalization_of_attack.json` 
- Models `evaluation/models/usenix_20`

**Expected results**

Appendix D  

```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/02_generalization_of_attack.py"```    

```
             USENIX '20 IEEE S&P '22
Success Rate     99.62%       99.67%
Running Time     7m 38s       7m 12s
L1               1032.5       1115.0
Linf               30.0         35.0
```
</details>
<details>
<summary>03 Scaling of target reviewer</summary>

Next, we scale the attack to larger sets of target reviewers and consider different combinations for selecting, rejecting, and substituting reviewers. We allow an attacker to select up to five target reviewers, which is equivalent to replacing all of the initially assigned reviewers. Furthermore, we allow the rejection of up to two reviewers. We focus again on close reviewers and randomly select 100 sets of targets per combination.

The experiment can be executed with:

```
WORKERS=100

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/scaling_of_target_reviewer.json --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name scaling-of-targets"
```

Raw results are saved @ `evaluation/trials/scaling-of-targets`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| #Targets |  CPU   | Disc Space | Memory (per target) |
|:--------:|:------:|:----------:|:-------------------:|
|   1700   | ~4900h |    22 GB   |        1900MB       |

**Prerequisites**
- Targets `evaluation/targets/scaling_of_target_reviewer.json` 
- Models `evaluation/models/victim`

**Expected results**

Appendix E 

```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/03_scaling_of_target_reviewer.py"```    

```
[+] Saved plot @ evaluation/plots/scaling-of-targets.pdf
```
</details>
<details>
<summary>04 All transformations</summary>

So far, we have focused on format-level transformations to realize manipulations. These transformations exploit intrinsics of the submission format, which effectively allows us to make arbitrary changes to a PDF file. An attacker likely has access to similar transformations in any practical setting. In fact, robust parsing of PDF files has been shown to be a hard problem. However, we believe it is important for an attacker to minimize any traces and consider different classes of transformations as introduced in Section 3.2.

The experiment can be executed with:

```
WORKERS=100
REPETITION_NO=1 # from [1,...,8] 

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/budget-vs-transformer.json --problem_space_block_features --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --workers ${WORKERS} --trial_name budget-vs-transformer-${REPETITION_NO}"
```

and

```
WORKERS=100
REPETITION_NO=1 # from [1,...,8] 

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/switches-vs-transformer.json --problem_space_block_features --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --workers ${WORKERS} --trial_name switches-vs-transformer-${REPETITION_NO}"
```

Note: For the full evaluation the runs were repeated at total of 8 times.

Raw results are saved @ `evaluation/trials/budget-vs-transformer-*` and `evaluation/trials/switches-vs-transformer-*`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| Mode           | #Targets |   CPU  | Disc Space | Memory (per target) |
|----------------|:--------:|:------:|:----------:|:-------------------:|
| Budget (x1)    |   1500   | ~1200h |    32 GB   |       ~2250MB       |
| Switches (x1)  |   1500   | ~1050h |    29 GB   |       ~2250MB       |
| Budget (full)  |  1500x8  | ~9500h |   256 GB   |       ~2250MB       |
| Switches (full)|  1500x8  | ~8350h |   232 GB   |       ~2250MB       |

**Prerequisites**
- Targets
    * `evaluation/targets/budget-vs-transformer.json` 
    * `evaluation/targets/switches-vs-transformer.json`
- Models `evaluation/models/victim`
- Problemspace 
    * `evaluation/problemspace/llms`
    * `evaluation/problemspace/synonyms`

**Expected results**

Appendix E and results inline in text

```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/04_all_transformations.py"```    

```
[+] Switches
                   1.00   2.00   4.00   8.00  16.00
    Text      :   24.25  30.00  36.00  40.62  48.12
    + Encoding:   24.38  32.25  37.38  44.62  51.75
    + Format  :   77.13  97.25  99.00  99.88 100.00

[+] Budget
                   0.25   0.50   1.00   2.00   4.00
    Text      :   21.62  28.25  40.75  51.88  67.13
    + Encoding:   25.12  30.38  44.25  53.75  68.62
    + Format  :   99.88 100.00  99.88  99.12  99.00
    
[+] Saved plot @ evaluation/plots/all-transformations.pdf
```
</details>
<details>
<summary>05 Surrogates</summary>

In practice, an attacker typically does not have unrestricted access to the target system. In the following, we therefore assume a black-box scenario and consider an adversary with only limited knowledge. In particular, this adversary cannot access the assignment system and its training data. Instead, we demonstrate that she could leverage her knowledge about the program committee and construct a surrogate dataset to train her own models for preparing adversarial papers.

The experiment can be executed with:

```
WORKERS=100
NO_SURROGATES=1 # from [1,...,8] 

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/surrogates/surrogate_targets_${NO_SURROGATES}.json --reviewer_window 2 --delta -0.16 --reviewer_offset 1 --no_successors 128 --beam_width 4 --step 256 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name surrogates-${NO_SURROGATES}"
```

Raw results are saved @ `evaluation/trials/surrogates-*`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| #Surrogates    | #Targets |   CPU  | Disc Space | Memory (per target) |
|----------------|:--------:|:------:|:----------:|:-------------------:|
|        1       |   2400   |  ~150h |    39 GB   |        ~600MB       |
|        2       |   2400   |  ~350h |    42 GB   |       ~1050MB       |
|        3       |   2400   |  ~600h |    44 GB   |       ~1500MB       |
|        4       |   2400   |  ~950h |    46 GB   |       ~1900MB       |
|        5       |   2400   | ~1750h |    49 GB   |       ~2250MB       |
|        6       |   2400   | ~2700h |    51 GB   |       ~2650MB       |
|        7       |   2400   | ~4450h |    53 GB   |       ~3050MB       |
|        8       |   2400   | ~5450h |    53 GB   |       ~3450MB       |


**Prerequisites**
- Targets
    * `evaluation/targets/surrogates/surrogate_targets_1.json` 
    * `evaluation/targets/surrogates/surrogate_targets_2.json`  
    * `evaluation/targets/surrogates/surrogate_targets_3.json` 
    * `evaluation/targets/surrogates/surrogate_targets_4.json` 
    * `evaluation/targets/surrogates/surrogate_targets_5.json` 
    * `evaluation/targets/surrogates/surrogate_targets_6.json` 
    * `evaluation/targets/surrogates/surrogate_targets_7.json`
    * `evaluation/targets/surrogates/surrogate_targets_8.json`
- Models 
  * `evaluation/models/victim`
  * `evaluation/models/overlap_0.70`

**Expected results**

1. Figure 5

    ```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/05_surrogates.py"```    

        [+] Saved plot @ evaluation/plots/surrogates.pdf
        

2. Appendix F and results inline in text  
    
    ```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/05_surrogates_appendix.py"```

        [+] Median L1 norm Selection
            1: 1990
            2: 3214
            4: 5218
            8: 7556

        [+] Median L1 norm Rejection
            1: 1300
            2: 2136
            4: 3040
            8: 3094
        
        [+] Median L1 norm Substitution
            1: 3843
            2: 5869
            4: 8470
            8: 12084

        [+] Saved plot @ evaluation/plots/surrogates_appendix.pdf
</details>
<details>
<summary>06 Transferability</summary>

To further study the transferability of our attack, we sample 100 target reviewer from the median ranking computed over 8 assignment systems and simulate the attack with an ensemble of 8 surrogates. 

The experiment can be executed with:

```
WORKERS=50

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/transferability.json --reviewer_window 2 --delta -0.16 --reviewer_offset 1 --no_successors 128 --beam_width 4 --step 256 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name transferability"
```

Raw results are saved @ `evaluation/trials/transferability`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| #Targets |  CPU  | Disc Space | Memory (per target) |
|:--------:|:-----:|:----------:|:-------------------:|
|    100   | ~300h |     2 GB   |       2700MB        |

**Prerequisites**
- Targets `evaluation/targets/surrogates/transferability.json`
- Models 
  * `evaluation/models/victim`
  * `evaluation/models/overlap_0.70`

**Expected results**

Figure 6 and results inline in text

```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/06_transferabillity.py"```    

```
[+] Cumulative: [99, 97, 96, 96, 90, 83, 67, 34]
[+] Saved plot @ evaluation/plots/transferability.pdf
```
</details>
<details>
<summary>07 Overlap</summary>

To understand the role of the surrogate corpus, we finally repeat the previous experiment with varying levels of overlap.

The experiment can be executed with:

```
WORKERS=40

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/overlap.json --reviewer_window 2 --delta -0.16 --reviewer_offset 1 --no_successors 128 --beam_width 4 --step 256 --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --trial_name overlap"
```

and

```
./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/07_overlap_cross_entropy.py"
```

Raw results are saved @ `evaluation/trials/overlap`  and `evaluation/trials/overlap_cross_entropy.json`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| #Targets |  CPU  | Disc Space | Memory (per target) |
|:--------:|:-----:|:----------:|:-------------------:|
|    400   | ~350h |     8 GB   |       3150MB        |

**Prerequisites**
- Targets `evaluation/targets/surrogates/overlap.json`
- Models 
  * `evaluation/models/victim`
  * `evaluation/models/overlap_0.00`
  * `evaluation/models/overlap_0.30`
  * `evaluation/models/overlap_0.70`
  * `evaluation/models/overlap_1.00`

**Expected results**

1. Results inline in text
    
    ```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/07_overlap.py"```    
        
        [+] Overlap
            -> 0.00: 82.8%
            -> 0.30: 79.6%
            -> 0.70: 80.0%
            -> 1.00: 78.0%

2. Appendix G

    ```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/07_overlap_cross_entropy_stats.py"```
    
        [+] Overlap
            1     13.19+-0.46     13.13+-0.47     13.12+-0.37     13.20+-0.44
            2     12.56+-0.29     12.55+-0.37     12.64+-0.34     12.50+-0.29
            3     13.58+-0.63     13.56+-0.56     13.47+-0.62     13.52+-0.63
            4     12.43+-0.50     12.29+-0.48     12.35+-0.54     12.32+-0.50 
            5     13.41+-0.51     13.41+-0.61     13.50+-0.56     13.31+-0.66
            6     12.84+-0.23     12.81+-0.21     12.93+-0.25     12.90+-0.23
            7     14.20+-0.42     14.28+-0.44     14.39+-0.48     14.08+-0.41 
            8     13.57+-0.46     13.59+-0.46     13.55+-0.40     13.66+-0.42 
            9     13.44+-0.72     13.33+-0.68     13.54+-0.67     13.44+-0.76 
            10    15.24+-0.59     15.08+-0.59     15.31+-0.66     14.88+-0.61

</details>
<details>
<summary>08 Commitee size</summary>

We simulate the attack with varying sizes of the program committee. 

The experiment can be executed with:

```
WORKERS=100

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/committees.json --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --trial_name committees"
```

Raw results are saved @ `evaluation/trials/committees`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| #Targets |   CPU   | Disc Space | Memory (per target) |
|:--------:|:-------:|:----------:|:-------------------:|
|  33600   |  ~9400h |   305 GB   |       1550MB        |

**Prerequisites**
- Targets `evaluation/targets/surrogates/committees.json`
- Models `evaluation/models/committees`

**Expected results**

Appendix H

```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/08_committees.py"```

```
[+] Saved plot @ evaluation/plots/committees.pdf
```
</details>
<details>
<summary>09 Load balancing</summary>

We simulate the attack with varying numbers of concurring submissions between 200 and 1,000.

The experiment can be executed with:

```
WORKERS=100

./docker.sh run "python3 /root/adversarial-papers/src/attack.py --targets_file /root/adversarial-papers/evaluation/targets/load_balancing.json --problem_space_block_features --feature_problem_switch 8 --format_level --workers ${WORKERS} --reviewer_window 6 --reviewer_offset 2 --no_successors 256 --beam_width 4 --step 64 --trial_name load_balancing"
```

and 

```
WORKERS=32

./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/09_load_balancing_assignments.py --trials_dir /root/adversarial-papers/plots/data/load_balancing --workers ${WORKERS} --name load_balancing"
```

Raw results are saved @ `evaluation/trials/load_balancing` and `evaluation/trials/load_balancing.json`

Adjust the number of workers according to your hardware setup.

**Hardware requirements**

| Mode           | #Targets |   CPU  | Disc Space | Memory (per target) |
|----------------|:--------:|:------:|:----------:|:-------------------:|
| Attack         |   33600  | ~3700h |    292 GB  |       ~1400MB       |
| Assignments    |   33600  |  ~350h |    -   GB  |       ~6000MB       |


**Prerequisites**
- Targets `evaluation/targets/surrogates/load_balancing.json`
- Models `evaluation/models/committees`
- Submissions `evaluation/corpus/committees_base.json`

**Expected results**

Appendix I

```./docker.sh run "python3 /root/adversarial-papers/evaluation/scripts/09_load_balancing.py"```

```
[+] Saved plot @ evaluation/plots/load_balancing.pdf
```
</details>


## Misc
<details>
<summary>Targets</summary>

Scripts for generating targets are located at `scripts/targets`.

These can be executed with

```
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/featurespace_search.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/generalization_of_attack.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/scaling_of_target_reviewer.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/all_transformations.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/surrogates.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/transferability.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/overlap.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/committees.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/load_balancing.py"
./docker.sh run "python3 /root/adversarial-papers/scripts/targets/hypersearch.py"
```

Results are stored at `evaluation/targets`
</details>

<details>
<summary>Hypersearch</summary>

The hyperparameter search is provided in a separate script `src/hypersearch.py` that orchestrates the main attack script and keeps track of all parameters.

It can be executed with

```
WORKERS=56
./docker.sh run "python3 /root/adversarial-papers/src/hypersearch.py --white_box --workers ${WORKERS} --workers_per_trial 8 --name white_box"
```

and 

```
WORKERS=56
./docker.sh run "python3 /root/adversarial-papers/src/hypersearch.py --black_box --workers ${WORKERS} --workers_per_trial 8 --name black_box"
```

Results are saved @ `evaluation/trials/_hyperparameter'
</details>
<details>
<summary>Train your own models</summary>

For our experiments, we consider models trained on three different corpora:
- IEEE S&P'22 (`oakland_22_large`)
- USENIX'20 (`usenix_20`)
- Security Papers (`committees_base` and `committees`)

Unfortunately, due to licensing issues, we cannot make these publicly available. If you want to crawl your own corpus, you can use the scripts located at `scripts/crawler`.

Given a suitable corpus, you can train your own model using the `src/autobid.py` script.

```
usage: autobid.py [-h] [--corpus_dir CORPUS_DIR] [--models_dir MODELS_DIR] [--no_models NO_MODELS] [--no_topics NO_TOPICS] [--passes PASSES] [--iterations ITERATIONS] [--workers WORKERS]

optional arguments:
  -h, --help            show this help message and exit
  --corpus_dir CORPUS_DIR
  --models_dir MODELS_DIR
  --no_models NO_MODELS
  --no_topics NO_TOPICS
  --passes PASSES
  --iterations ITERATIONS
  --workers WORKERS
```

For example, the USENIX models can be trained via

```
./docker.sh run "python3 /root/adversarial-papers/src/autobid.py --corpus_dir /root/adversarial-papers/evaluation/corpus/usenix_20 --models_dir /root/adversarial-papers/evaluation/models/usenix
```
</details>
<details>
<summary>Scripts</summary>

Additional helper scripts are located at `scripts`
- `scripts/load_balancing`
- `scripts/morphing`
- `scripts/reviewer_words`
- `scripts/submissions`
- `scripts/corpus`
</details>
