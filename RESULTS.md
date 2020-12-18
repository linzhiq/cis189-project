# Performance Profile of Our Solver

## Motivation
Since this solver was built with the ultimate dream of running it at web scale, we discuss the effect changing properties about the input and the constraints of the solver on its performance.

### Number of Workers
We run our solver on 9 fast examples and one slow example, varying the number of workers. The solver was run on a 4 core i7 CPU, so there were 4 logical processors available. The time in seconds averaged over 5 epochs to solve for the optimal solution can be seen below.

|Workers |Avg Time (Fast) |Avg Time (Slow)|
|--------|----------------|------|
|1	|0.089	|8.22|
|2	|0.055	|1.97|
|3	|0.058	|0.44|
|4	|0.053	|4.21|
|5	|0.054  |3.18|
|6	|0.051	|2.70|
|8	|0.058	|3.89|

For the fast example, the avg time is the averaged solve time over 9 different tasks, while for the slow example there is a single slow example and hence, a single time to measure.

We believe that 3 cores perform the best because the solver was run on a testbench with 4 logical cores: 1 core was saddled with background processes while 3 other cores were free to search the search space. This is supported by the fact that the times we observed with greater than or equal to 4 workers were volatile: sometimes they were as fast as .05, sometimes they were as slow as 9 seconds. More workers than 3 have to contend with other background programs and each other for system resources. As such, the distribution of scores may vary depending on your testbench characteristics, though we expect to see similar volativity in time results as the number of workers you run approach the number of physical cores you have.

### Limiting Execution Time
Since in a web environment there's often limited execution time, we wanted to see what effect limiting the execution time would have on our various utility variables. The utility variables produced running on our slow example at various execution time limits have been tabulated below:

|Time	|Num Tasks	|Total Priority	|Tot_Tasks - (Max Load - Min Load)|
|--------|----------------|------|-----|
0.1	|25	|12|	36|
0.25	|25	|16|	36|
0.5	|25|	16|	36|
1	|25	|19|	36|

Num tasks is maximized first, as expected.
