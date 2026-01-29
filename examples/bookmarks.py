"""Browser bookmarks organized by topic - URLs and descriptions."""

from loopy import Loopy


def bookmarks() -> Loopy:
    """
    A bookmarks manager demonstrating URL organization.

    Use cases for LLMs:
    - "Save this article about Python to my programming bookmarks"
    - "Find all my machine learning resources"
    - "Organize my unsorted bookmarks into appropriate folders"
    - "What cooking sites have I bookmarked?"
    """
    return (
        Loopy()
        # Programming
        .mkdir("/programming/python/tutorials", parents=True)
        .mkdir("/programming/python/libraries", parents=True)
        .mkdir("/programming/python/tools", parents=True)
        .mkdir("/programming/javascript/frameworks", parents=True)
        .mkdir("/programming/javascript/tutorials", parents=True)
        .mkdir("/programming/rust", parents=True)
        .mkdir("/programming/devops/docker", parents=True)
        .mkdir("/programming/devops/kubernetes", parents=True)

        .touch("/programming/python/tutorials/real_python", "https://realpython.com|Comprehensive Python tutorials and articles")
        .touch("/programming/python/tutorials/python_docs", "https://docs.python.org|Official Python documentation")
        .touch("/programming/python/libraries/awesome_python", "https://github.com/vinta/awesome-python|Curated list of Python frameworks and libraries")
        .touch("/programming/python/tools/uv", "https://github.com/astral-sh/uv|Fast Python package installer")
        .touch("/programming/python/tools/ruff", "https://github.com/astral-sh/ruff|Fast Python linter")
        .touch("/programming/javascript/frameworks/react_docs", "https://react.dev|Official React documentation")
        .touch("/programming/javascript/frameworks/nextjs", "https://nextjs.org|React framework for production")
        .touch("/programming/javascript/tutorials/javascript_info", "https://javascript.info|Modern JavaScript tutorial")
        .touch("/programming/rust/rust_book", "https://doc.rust-lang.org/book|The Rust Programming Language book")
        .touch("/programming/rust/rustlings", "https://github.com/rust-lang/rustlings|Small Rust exercises")
        .touch("/programming/devops/docker/docker_docs", "https://docs.docker.com|Official Docker documentation")
        .touch("/programming/devops/kubernetes/k8s_docs", "https://kubernetes.io/docs|Kubernetes documentation")

        # AI & Machine Learning
        .mkdir("/ai/llms/papers", parents=True)
        .mkdir("/ai/llms/tools", parents=True)
        .mkdir("/ai/llms/tutorials", parents=True)
        .mkdir("/ai/ml_fundamentals", parents=True)
        .mkdir("/ai/computer_vision", parents=True)
        .mkdir("/ai/datasets", parents=True)

        .touch("/ai/llms/papers/attention_paper", "https://arxiv.org/abs/1706.03762|Attention Is All You Need - Transformer paper")
        .touch("/ai/llms/papers/gpt3_paper", "https://arxiv.org/abs/2005.14165|Language Models are Few-Shot Learners")
        .touch("/ai/llms/tools/anthropic_docs", "https://docs.anthropic.com|Anthropic API documentation")
        .touch("/ai/llms/tools/openai_docs", "https://platform.openai.com/docs|OpenAI API documentation")
        .touch("/ai/llms/tools/langchain", "https://python.langchain.com|LangChain framework docs")
        .touch("/ai/llms/tutorials/prompt_engineering", "https://www.promptingguide.ai|Prompt engineering guide")
        .touch("/ai/ml_fundamentals/fastai", "https://www.fast.ai|Practical deep learning course")
        .touch("/ai/ml_fundamentals/3blue1brown_nn", "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi|Neural networks explained visually")
        .touch("/ai/computer_vision/yolo", "https://pjreddie.com/darknet/yolo|YOLO object detection")
        .touch("/ai/datasets/huggingface", "https://huggingface.co/datasets|Hugging Face datasets hub")
        .touch("/ai/datasets/kaggle", "https://www.kaggle.com/datasets|Kaggle datasets")

        # Reading
        .mkdir("/reading/news/tech", parents=True)
        .mkdir("/reading/news/world", parents=True)
        .mkdir("/reading/blogs/tech", parents=True)
        .mkdir("/reading/blogs/personal", parents=True)
        .mkdir("/reading/newsletters", parents=True)

        .touch("/reading/news/tech/hacker_news", "https://news.ycombinator.com|Tech news and discussions")
        .touch("/reading/news/tech/techmeme", "https://www.techmeme.com|Tech news aggregator")
        .touch("/reading/news/tech/ars_technica", "https://arstechnica.com|In-depth tech journalism")
        .touch("/reading/news/world/reuters", "https://www.reuters.com|International news")
        .touch("/reading/blogs/tech/paul_graham", "http://paulgraham.com/articles.html|Paul Graham essays")
        .touch("/reading/blogs/tech/stratechery", "https://stratechery.com|Tech business analysis")
        .touch("/reading/blogs/personal/wait_but_why", "https://waitbutwhy.com|Long-form explainers on everything")
        .touch("/reading/newsletters/morning_brew", "https://www.morningbrew.com|Daily business news digest")

        # Reference
        .mkdir("/reference/documentation", parents=True)
        .mkdir("/reference/cheatsheets", parents=True)
        .mkdir("/reference/tools", parents=True)

        .touch("/reference/documentation/mdn", "https://developer.mozilla.org|Mozilla Developer Network - web docs")
        .touch("/reference/documentation/devdocs", "https://devdocs.io|API documentation browser")
        .touch("/reference/cheatsheets/tldr", "https://tldr.sh|Simplified man pages")
        .touch("/reference/cheatsheets/cheat_sh", "https://cheat.sh|Cheat sheets for commands")
        .touch("/reference/tools/regex101", "https://regex101.com|Regex tester and debugger")
        .touch("/reference/tools/json_formatter", "https://jsonformatter.org|JSON formatter and validator")
        .touch("/reference/tools/crontab_guru", "https://crontab.guru|Cron expression editor")

        # Cooking
        .mkdir("/cooking/recipes/quick_meals", parents=True)
        .mkdir("/cooking/recipes/baking", parents=True)
        .mkdir("/cooking/recipes/cuisines", parents=True)
        .mkdir("/cooking/techniques", parents=True)

        .touch("/cooking/recipes/quick_meals/serious_eats", "https://www.seriouseats.com|Science-based cooking")
        .touch("/cooking/recipes/quick_meals/budget_bytes", "https://www.budgetbytes.com|Budget-friendly recipes")
        .touch("/cooking/recipes/baking/king_arthur", "https://www.kingarthurbaking.com/recipes|Baking recipes and guides")
        .touch("/cooking/recipes/cuisines/just_one_cookbook", "https://www.justonecookbook.com|Japanese home cooking")
        .touch("/cooking/recipes/cuisines/woks_of_life", "https://thewoksoflife.com|Chinese family recipes")
        .touch("/cooking/techniques/food_lab", "https://www.seriouseats.com/the-food-lab|J. Kenji Lopez-Alt cooking science")

        # Unsorted (for LLM to organize)
        .mkdir("/unsorted", parents=True)
        .touch("/unsorted/link1", "https://www.postgresql.org/docs|PostgreSQL documentation")
        .touch("/unsorted/link2", "https://www.typescriptlang.org|TypeScript language")
        .touch("/unsorted/link3", "https://www.nytimes.com/section/food|NYT Food section")
        .touch("/unsorted/link4", "https://remix.run|Remix web framework")
        .touch("/unsorted/link5", "https://www.allrecipes.com|Recipe search engine")
    )


if __name__ == "__main__":
    tree = bookmarks()
    print(tree.tree("/"))
