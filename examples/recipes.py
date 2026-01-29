"""Recipe database organized by cuisine, course, and dietary needs."""

from loopy import Loopy


def recipes() -> Loopy:
    """
    A recipe collection demonstrating multi-dimensional categorization.

    Use cases for LLMs:
    - "Find me a quick vegetarian dinner"
    - "What Italian dishes can I make with chicken?"
    - "Add this recipe to the appropriate categories"
    - "What ingredients do I need for pad thai?"
    - "Suggest a meal plan for the week"
    """
    return (
        Loopy()
        # By cuisine
        .mkdir("/cuisine/italian/pasta", parents=True)
        .mkdir("/cuisine/italian/pizza", parents=True)
        .mkdir("/cuisine/italian/risotto", parents=True)
        .mkdir("/cuisine/mexican/tacos", parents=True)
        .mkdir("/cuisine/mexican/burritos", parents=True)
        .mkdir("/cuisine/asian/chinese", parents=True)
        .mkdir("/cuisine/asian/japanese", parents=True)
        .mkdir("/cuisine/asian/thai", parents=True)
        .mkdir("/cuisine/asian/indian", parents=True)
        .mkdir("/cuisine/american/bbq", parents=True)
        .mkdir("/cuisine/american/comfort", parents=True)
        .mkdir("/cuisine/mediterranean", parents=True)

        # By course
        .mkdir("/course/breakfast", parents=True)
        .mkdir("/course/lunch", parents=True)
        .mkdir("/course/dinner", parents=True)
        .mkdir("/course/appetizers", parents=True)
        .mkdir("/course/desserts", parents=True)
        .mkdir("/course/snacks", parents=True)

        # By diet
        .mkdir("/diet/vegetarian", parents=True)
        .mkdir("/diet/vegan", parents=True)
        .mkdir("/diet/gluten_free", parents=True)
        .mkdir("/diet/keto", parents=True)
        .mkdir("/diet/dairy_free", parents=True)

        # By time
        .mkdir("/time/under_15min", parents=True)
        .mkdir("/time/under_30min", parents=True)
        .mkdir("/time/under_60min", parents=True)
        .mkdir("/time/meal_prep", parents=True)

        # Italian recipes
        .touch("/cuisine/italian/pasta/carbonara", "time:25min|servings:4|difficulty:medium|ingredients:spaghetti,eggs,pecorino,guanciale,black_pepper|tags:classic,creamy|also:/course/dinner,/time/under_30min")
        .touch("/cuisine/italian/pasta/cacio_e_pepe", "time:20min|servings:2|difficulty:medium|ingredients:spaghetti,pecorino,black_pepper|tags:simple,vegetarian|also:/diet/vegetarian,/time/under_30min")
        .touch("/cuisine/italian/pasta/pesto_pasta", "time:15min|servings:4|difficulty:easy|ingredients:pasta,basil,pine_nuts,parmesan,garlic,olive_oil|tags:fresh,summer|also:/diet/vegetarian,/time/under_15min")
        .touch("/cuisine/italian/pizza/margherita", "time:45min|servings:2|difficulty:medium|ingredients:dough,tomatoes,mozzarella,basil|tags:classic,vegetarian|also:/diet/vegetarian,/course/dinner")
        .touch("/cuisine/italian/risotto/mushroom_risotto", "time:40min|servings:4|difficulty:medium|ingredients:arborio_rice,mushrooms,parmesan,white_wine,stock|tags:creamy,vegetarian|also:/diet/vegetarian,/course/dinner")

        # Mexican recipes
        .touch("/cuisine/mexican/tacos/carnitas", "time:4hrs|servings:8|difficulty:easy|ingredients:pork_shoulder,orange,lime,cumin,oregano|tags:slow_cooked,crowd_pleaser|also:/course/dinner,/diet/gluten_free")
        .touch("/cuisine/mexican/tacos/fish_tacos", "time:25min|servings:4|difficulty:easy|ingredients:white_fish,cabbage,lime_crema,corn_tortillas|tags:light,fresh|also:/course/dinner,/time/under_30min")
        .touch("/cuisine/mexican/tacos/veggie_tacos", "time:20min|servings:4|difficulty:easy|ingredients:black_beans,corn,peppers,avocado,salsa|tags:healthy,quick|also:/diet/vegan,/diet/vegetarian,/time/under_30min")
        .touch("/cuisine/mexican/burritos/breakfast_burrito", "time:15min|servings:2|difficulty:easy|ingredients:eggs,cheese,beans,salsa,tortilla|tags:filling,protein|also:/course/breakfast,/time/under_15min")

        # Asian recipes
        .touch("/cuisine/asian/chinese/kung_pao_chicken", "time:30min|servings:4|difficulty:medium|ingredients:chicken,peanuts,chili,sichuan_peppercorn,soy_sauce|tags:spicy,classic|also:/course/dinner,/time/under_30min")
        .touch("/cuisine/asian/chinese/fried_rice", "time:15min|servings:4|difficulty:easy|ingredients:rice,eggs,soy_sauce,vegetables,green_onion|tags:quick,use_leftovers|also:/time/under_15min,/course/dinner")
        .touch("/cuisine/asian/chinese/mapo_tofu", "time:25min|servings:4|difficulty:medium|ingredients:tofu,ground_pork,doubanjiang,sichuan_peppercorn|tags:spicy,numbing|also:/course/dinner,/time/under_30min")
        .touch("/cuisine/asian/japanese/teriyaki_salmon", "time:20min|servings:2|difficulty:easy|ingredients:salmon,soy_sauce,mirin,sake,ginger|tags:healthy,quick|also:/diet/gluten_free,/time/under_30min")
        .touch("/cuisine/asian/japanese/miso_soup", "time:10min|servings:4|difficulty:easy|ingredients:dashi,miso,tofu,wakame,green_onion|tags:light,traditional|also:/diet/vegetarian,/time/under_15min")
        .touch("/cuisine/asian/thai/pad_thai", "time:30min|servings:4|difficulty:medium|ingredients:rice_noodles,shrimp,eggs,tamarind,fish_sauce,peanuts,bean_sprouts|tags:classic,sweet_sour|also:/course/dinner,/time/under_30min")
        .touch("/cuisine/asian/thai/green_curry", "time:35min|servings:4|difficulty:medium|ingredients:green_curry_paste,coconut_milk,chicken,thai_basil,vegetables|tags:creamy,spicy|also:/diet/gluten_free,/course/dinner")
        .touch("/cuisine/asian/indian/butter_chicken", "time:45min|servings:6|difficulty:medium|ingredients:chicken,tomatoes,cream,butter,garam_masala,ginger,garlic|tags:creamy,mild|also:/diet/gluten_free,/course/dinner")
        .touch("/cuisine/asian/indian/dal", "time:40min|servings:6|difficulty:easy|ingredients:lentils,tomatoes,onion,cumin,turmeric,ginger|tags:protein,comfort|also:/diet/vegan,/diet/vegetarian,/diet/gluten_free")
        .touch("/cuisine/asian/indian/chana_masala", "time:30min|servings:4|difficulty:easy|ingredients:chickpeas,tomatoes,onion,garam_masala,cumin|tags:protein,vegan|also:/diet/vegan,/diet/vegetarian,/time/under_30min")

        # American recipes
        .touch("/cuisine/american/bbq/pulled_pork", "time:8hrs|servings:12|difficulty:easy|ingredients:pork_shoulder,bbq_rub,apple_cider_vinegar|tags:slow_cooked,crowd_pleaser|also:/diet/gluten_free,/time/meal_prep")
        .touch("/cuisine/american/bbq/smash_burger", "time:15min|servings:4|difficulty:easy|ingredients:ground_beef,cheese,onion,pickles,buns|tags:quick,indulgent|also:/course/dinner,/time/under_15min")
        .touch("/cuisine/american/comfort/mac_and_cheese", "time:30min|servings:6|difficulty:easy|ingredients:macaroni,cheddar,milk,butter|tags:classic,kid_friendly|also:/diet/vegetarian,/course/dinner,/time/under_30min")
        .touch("/cuisine/american/comfort/chicken_soup", "time:60min|servings:8|difficulty:easy|ingredients:chicken,carrots,celery,noodles,onion|tags:healing,comfort|also:/course/dinner,/time/meal_prep")

        # Mediterranean
        .touch("/cuisine/mediterranean/greek_salad", "time:10min|servings:4|difficulty:easy|ingredients:cucumber,tomato,feta,olives,red_onion,oregano|tags:fresh,no_cook|also:/diet/vegetarian,/diet/gluten_free,/time/under_15min,/course/lunch")
        .touch("/cuisine/mediterranean/falafel", "time:45min|servings:6|difficulty:medium|ingredients:chickpeas,parsley,cumin,garlic,onion|tags:crispy,protein|also:/diet/vegan,/diet/vegetarian")
        .touch("/cuisine/mediterranean/shakshuka", "time:25min|servings:4|difficulty:easy|ingredients:eggs,tomatoes,peppers,onion,cumin,paprika|tags:one_pan,brunch|also:/diet/vegetarian,/diet/gluten_free,/course/breakfast,/time/under_30min")
        .touch("/cuisine/mediterranean/hummus", "time:10min|servings:8|difficulty:easy|ingredients:chickpeas,tahini,lemon,garlic,olive_oil|tags:dip,protein|also:/diet/vegan,/diet/gluten_free,/course/appetizers,/time/under_15min")

        # Breakfast
        .touch("/course/breakfast/overnight_oats", "time:5min|servings:1|difficulty:easy|ingredients:oats,milk,yogurt,honey,fruit|tags:meal_prep,healthy|also:/diet/vegetarian,/time/under_15min,/time/meal_prep")
        .touch("/course/breakfast/avocado_toast", "time:10min|servings:2|difficulty:easy|ingredients:bread,avocado,eggs,lemon,chili_flakes|tags:trendy,healthy|also:/diet/vegetarian,/time/under_15min")
        .touch("/course/breakfast/smoothie_bowl", "time:10min|servings:1|difficulty:easy|ingredients:frozen_fruit,banana,milk,granola,toppings|tags:healthy,customizable|also:/diet/vegan,/time/under_15min")

        # Desserts
        .touch("/course/desserts/chocolate_chip_cookies", "time:30min|servings:24|difficulty:easy|ingredients:flour,butter,sugar,eggs,chocolate_chips|tags:classic,baking|also:/diet/vegetarian")
        .touch("/course/desserts/tiramisu", "time:30min|servings:8|difficulty:medium|ingredients:ladyfingers,mascarpone,espresso,cocoa,eggs|tags:italian,no_bake|also:/diet/vegetarian,/cuisine/italian")
        .touch("/course/desserts/mango_sticky_rice", "time:45min|servings:4|difficulty:medium|ingredients:sticky_rice,coconut_milk,mango,sugar|tags:thai,tropical|also:/diet/vegan,/diet/gluten_free,/cuisine/asian/thai")
    )


if __name__ == "__main__":
    tree = recipes()
    print(tree.tree("/cuisine"))
