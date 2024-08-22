# Frontend for Expert Evaluation

### Introduction
We have a total of 291 experiments to consider. Each of them must be checked for correctness. Additionally, we also want to evaluate understandability. To facilitate this, I created 5-tuples using Aleksandr's [repository](https://github.com/WSE-research/cross-national-entity-ranking-crowdsourcing). If I use the BWS multiplier of 2, it results in 583 experiments. With a multiplier of 1.0, there are 292 experiments. Thus, this would have resulted in 874 (with a multiplier of 2) or 583 (with a multiplier of 1) experiments to evaluate. To reduce this number further, I set the multiplier to 0.5. Now, there are 146 attempts for understandability (5-tuple) and 291 attempts for correctness, with the latter number being fixed.

### Usage
1. Login with the provided **ID**.
2. Read the introduction for both metrics/experiment types.
3. Assess the experiments.

   3.1 **Correctness**:
   - Count the errors with respect to the provided datasets.
   - Enter the value.
   - Click either "next" or "previous" to store your input and switch to another explanation.

   3.2 **Understandability**:
   - Check all explanations and select one as the worst and one as the best.
   - Click either "next" or "previous" to store your input and switch to another explanation-tuple.

4. **Finish**:
   - On the sidebar, you can see your progress.
   - You can change ratings at any time.
   - The evaluation is considered complete when both metrics are at X/X or Y/Y.
