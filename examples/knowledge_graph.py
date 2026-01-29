"""A knowledge graph of concepts and their relationships."""

from loopy import Loopy


def knowledge_graph() -> Loopy:
    """
    A knowledge ontology showing concept hierarchies and relationships.

    Use cases for LLMs:
    - "What is the relationship between Neural Networks and Deep Learning?"
    - "List all programming paradigms"
    - "Add a new concept under /science/physics"
    - "Find concepts related to 'optimization'"
    - "What are the prerequisites for learning Transformers?"
    """
    return (
        Loopy()
        # Computer Science
        .mkdir("/concepts/cs/programming_paradigms/functional", parents=True)
        .mkdir("/concepts/cs/programming_paradigms/oop", parents=True)
        .mkdir("/concepts/cs/programming_paradigms/declarative", parents=True)
        .mkdir("/concepts/cs/programming_paradigms/imperative", parents=True)
        .mkdir("/concepts/cs/data_structures/linear", parents=True)
        .mkdir("/concepts/cs/data_structures/trees", parents=True)
        .mkdir("/concepts/cs/data_structures/graphs", parents=True)
        .mkdir("/concepts/cs/algorithms/sorting", parents=True)
        .mkdir("/concepts/cs/algorithms/searching", parents=True)
        .mkdir("/concepts/cs/algorithms/optimization", parents=True)
        .mkdir("/concepts/cs/algorithms/graph_algorithms", parents=True)

        # Programming paradigms
        .touch("/concepts/cs/programming_paradigms/functional/pure_functions", "def:Functions without side effects|related:immutability,referential_transparency")
        .touch("/concepts/cs/programming_paradigms/functional/immutability", "def:Data that cannot be changed after creation|related:pure_functions,persistent_data_structures")
        .touch("/concepts/cs/programming_paradigms/functional/higher_order_functions", "def:Functions that take or return functions|examples:map,filter,reduce")
        .touch("/concepts/cs/programming_paradigms/oop/encapsulation", "def:Bundling data with methods that operate on it|related:information_hiding")
        .touch("/concepts/cs/programming_paradigms/oop/inheritance", "def:Mechanism for code reuse through class hierarchies|related:polymorphism")
        .touch("/concepts/cs/programming_paradigms/oop/polymorphism", "def:Same interface for different underlying types|types:ad-hoc,parametric,subtype")

        # Data structures
        .touch("/concepts/cs/data_structures/linear/array", "def:Contiguous memory block|access:O(1)|insert:O(n)|use_when:random_access_needed")
        .touch("/concepts/cs/data_structures/linear/linked_list", "def:Nodes connected by pointers|access:O(n)|insert:O(1)|use_when:frequent_insertions")
        .touch("/concepts/cs/data_structures/linear/stack", "def:LIFO structure|ops:push,pop,peek|use_when:undo_operations,parsing")
        .touch("/concepts/cs/data_structures/linear/queue", "def:FIFO structure|ops:enqueue,dequeue|use_when:task_scheduling,BFS")
        .touch("/concepts/cs/data_structures/trees/binary_tree", "def:Tree with max 2 children per node|related:BST,heap,trie")
        .touch("/concepts/cs/data_structures/trees/bst", "def:Binary tree with ordering property|search:O(log n)|prereq:binary_tree")
        .touch("/concepts/cs/data_structures/trees/heap", "def:Complete binary tree with heap property|use_when:priority_queue|prereq:binary_tree")
        .touch("/concepts/cs/data_structures/graphs/adjacency_list", "def:Graph as list of neighbors|space:O(V+E)|use_when:sparse_graphs")
        .touch("/concepts/cs/data_structures/graphs/adjacency_matrix", "def:Graph as 2D matrix|space:O(V^2)|use_when:dense_graphs")

        # Algorithms
        .touch("/concepts/cs/algorithms/sorting/quicksort", "def:Divide-and-conquer sorting|time:O(n log n) avg|space:O(log n)|prereq:recursion")
        .touch("/concepts/cs/algorithms/sorting/mergesort", "def:Stable divide-and-conquer sort|time:O(n log n)|space:O(n)|prereq:recursion")
        .touch("/concepts/cs/algorithms/searching/binary_search", "def:Search in sorted array|time:O(log n)|prereq:sorted_data")
        .touch("/concepts/cs/algorithms/optimization/dynamic_programming", "def:Solving problems by combining subproblem solutions|prereq:recursion,memoization|examples:fibonacci,knapsack")
        .touch("/concepts/cs/algorithms/optimization/greedy", "def:Making locally optimal choices|examples:huffman,dijkstra|when_works:optimal_substructure,greedy_choice")
        .touch("/concepts/cs/algorithms/graph_algorithms/bfs", "def:Level-by-level graph traversal|time:O(V+E)|use_when:shortest_path_unweighted|prereq:queue,graphs")
        .touch("/concepts/cs/algorithms/graph_algorithms/dfs", "def:Deep graph traversal|time:O(V+E)|use_when:cycle_detection,topological_sort|prereq:stack,graphs")
        .touch("/concepts/cs/algorithms/graph_algorithms/dijkstra", "def:Shortest path in weighted graph|time:O(V^2) or O(E log V)|prereq:heap,graphs,greedy")

        # Machine Learning
        .mkdir("/concepts/ml/supervised/classification", parents=True)
        .mkdir("/concepts/ml/supervised/regression", parents=True)
        .mkdir("/concepts/ml/unsupervised/clustering", parents=True)
        .mkdir("/concepts/ml/unsupervised/dimensionality_reduction", parents=True)
        .mkdir("/concepts/ml/deep_learning/architectures", parents=True)
        .mkdir("/concepts/ml/deep_learning/training", parents=True)
        .mkdir("/concepts/ml/deep_learning/nlp", parents=True)
        .mkdir("/concepts/ml/deep_learning/vision", parents=True)

        # ML fundamentals
        .touch("/concepts/ml/supervised/classification/logistic_regression", "def:Linear classifier with sigmoid|use_when:binary_classification|prereq:linear_algebra,calculus")
        .touch("/concepts/ml/supervised/classification/decision_tree", "def:Tree-based classifier|pros:interpretable|cons:overfitting|prereq:information_theory")
        .touch("/concepts/ml/supervised/classification/svm", "def:Maximum margin classifier|kernel_trick:nonlinear_boundaries|prereq:optimization,linear_algebra")
        .touch("/concepts/ml/supervised/regression/linear_regression", "def:Fitting a line to data|loss:MSE|prereq:linear_algebra,statistics")
        .touch("/concepts/ml/unsupervised/clustering/kmeans", "def:Partition into k clusters|prereq:distance_metrics|limitation:must_specify_k")
        .touch("/concepts/ml/unsupervised/dimensionality_reduction/pca", "def:Project to principal components|prereq:linear_algebra,eigenvalues|use_when:visualization,noise_reduction")

        # Deep learning
        .touch("/concepts/ml/deep_learning/architectures/perceptron", "def:Single layer neural unit|prereq:linear_algebra|leads_to:neural_networks")
        .touch("/concepts/ml/deep_learning/architectures/mlp", "def:Multi-layer perceptron|prereq:perceptron,backpropagation|universal_approximator:yes")
        .touch("/concepts/ml/deep_learning/architectures/cnn", "def:Convolutional neural network|use_for:images,spatial_data|prereq:mlp,convolution")
        .touch("/concepts/ml/deep_learning/architectures/rnn", "def:Recurrent neural network|use_for:sequences|problem:vanishing_gradient|prereq:mlp")
        .touch("/concepts/ml/deep_learning/architectures/lstm", "def:Long short-term memory|solves:vanishing_gradient|prereq:rnn|has:gates")
        .touch("/concepts/ml/deep_learning/architectures/transformer", "def:Attention-based architecture|prereq:attention,mlp|breakthrough:parallelization|paper:attention_is_all_you_need")
        .touch("/concepts/ml/deep_learning/training/backpropagation", "def:Gradient computation via chain rule|prereq:calculus,computational_graphs")
        .touch("/concepts/ml/deep_learning/training/gradient_descent", "def:Iterative optimization|variants:sgd,adam,rmsprop|prereq:calculus")
        .touch("/concepts/ml/deep_learning/training/regularization", "def:Preventing overfitting|techniques:dropout,weight_decay,batch_norm")
        .touch("/concepts/ml/deep_learning/nlp/attention", "def:Weighted focus mechanism|types:self,cross,multi-head|prereq:mlp,sequences")
        .touch("/concepts/ml/deep_learning/nlp/embeddings", "def:Dense vector representations|examples:word2vec,GloVe,BERT|prereq:linear_algebra")
        .touch("/concepts/ml/deep_learning/nlp/llm", "def:Large language model|examples:GPT,Claude,Llama|prereq:transformer,embeddings,scale")
        .touch("/concepts/ml/deep_learning/vision/convolution", "def:Sliding window feature extraction|prereq:linear_algebra|use_in:cnn")
        .touch("/concepts/ml/deep_learning/vision/pooling", "def:Downsampling operation|types:max,average|purpose:translation_invariance")

        # Mathematics
        .mkdir("/concepts/math/linear_algebra", parents=True)
        .mkdir("/concepts/math/calculus", parents=True)
        .mkdir("/concepts/math/probability", parents=True)
        .mkdir("/concepts/math/statistics", parents=True)

        .touch("/concepts/math/linear_algebra/vectors", "def:Ordered list of numbers|ops:addition,scalar_mult,dot_product")
        .touch("/concepts/math/linear_algebra/matrices", "def:2D array of numbers|ops:multiplication,transpose,inverse|prereq:vectors")
        .touch("/concepts/math/linear_algebra/eigenvalues", "def:Scalar that satisfies Av=λv|use_in:PCA,stability_analysis|prereq:matrices")
        .touch("/concepts/math/calculus/derivatives", "def:Rate of change|use_in:optimization,backpropagation")
        .touch("/concepts/math/calculus/chain_rule", "def:Derivative of composed functions|essential_for:backpropagation|prereq:derivatives")
        .touch("/concepts/math/calculus/gradient", "def:Vector of partial derivatives|use_in:gradient_descent|prereq:derivatives,vectors")
        .touch("/concepts/math/probability/bayes_theorem", "def:P(A|B) = P(B|A)P(A)/P(B)|foundation_of:bayesian_inference")
        .touch("/concepts/math/probability/distributions", "def:Probability over outcomes|common:normal,bernoulli,poisson")
        .touch("/concepts/math/statistics/hypothesis_testing", "def:Statistical inference method|concepts:p-value,significance,confidence_interval")

        # Learning paths (meta-organization)
        .mkdir("/paths", parents=True)
        .touch("/paths/ml_beginner", "1:/concepts/math/linear_algebra|2:/concepts/math/calculus|3:/concepts/ml/supervised|4:/concepts/ml/deep_learning/architectures/mlp")
        .touch("/paths/nlp_engineer", "1:/concepts/ml/deep_learning/nlp/embeddings|2:/concepts/ml/deep_learning/nlp/attention|3:/concepts/ml/deep_learning/architectures/transformer|4:/concepts/ml/deep_learning/nlp/llm")
        .touch("/paths/algorithms_prep", "1:/concepts/cs/data_structures|2:/concepts/cs/algorithms/sorting|3:/concepts/cs/algorithms/searching|4:/concepts/cs/algorithms/graph_algorithms")
    )


if __name__ == "__main__":
    tree = knowledge_graph()
    print(tree.tree("/concepts/ml"))
