"""E-commerce product taxonomy - categories, subcategories, and products."""

from loopy import Loopy


def product_catalog() -> Loopy:
    """
    A product catalog demonstrating hierarchical categorization.

    Use cases for LLMs:
    - "Add a new product under /clothing/shoes"
    - "Find all products under $50"
    - "Move 'running_shoes' from /clothing/shoes to /sports/footwear"
    - "What categories have the most products?"
    """
    return (
        Loopy()
        # Clothing
        .mkdir("/clothing/mens/shirts", parents=True)
        .mkdir("/clothing/mens/pants", parents=True)
        .mkdir("/clothing/mens/shoes", parents=True)
        .mkdir("/clothing/womens/dresses", parents=True)
        .mkdir("/clothing/womens/tops", parents=True)
        .mkdir("/clothing/womens/shoes", parents=True)
        .mkdir("/clothing/kids/boys", parents=True)
        .mkdir("/clothing/kids/girls", parents=True)

        # Men's products
        .touch("/clothing/mens/shirts/oxford_blue", "price:59.99|size:S,M,L,XL|color:blue|material:cotton")
        .touch("/clothing/mens/shirts/casual_white", "price:39.99|size:M,L,XL|color:white|material:linen")
        .touch("/clothing/mens/pants/chinos_khaki", "price:79.99|size:30,32,34,36|color:khaki|material:cotton")
        .touch("/clothing/mens/pants/jeans_dark", "price:89.99|size:30,32,34|color:indigo|material:denim")
        .touch("/clothing/mens/shoes/loafers_brown", "price:129.99|size:8,9,10,11,12|color:brown|material:leather")

        # Women's products
        .touch("/clothing/womens/dresses/summer_floral", "price:69.99|size:XS,S,M,L|color:multicolor|material:rayon")
        .touch("/clothing/womens/dresses/cocktail_black", "price:149.99|size:S,M,L|color:black|material:silk")
        .touch("/clothing/womens/tops/blouse_cream", "price:49.99|size:XS,S,M,L,XL|color:cream|material:polyester")
        .touch("/clothing/womens/shoes/heels_red", "price:119.99|size:6,7,8,9,10|color:red|material:patent_leather")

        # Kids products
        .touch("/clothing/kids/boys/tshirt_dino", "price:19.99|size:4,6,8,10|color:green|material:cotton")
        .touch("/clothing/kids/girls/dress_princess", "price:34.99|size:4,6,8|color:pink|material:tulle")

        # Electronics
        .mkdir("/electronics/computers/laptops", parents=True)
        .mkdir("/electronics/computers/desktops", parents=True)
        .mkdir("/electronics/phones/smartphones", parents=True)
        .mkdir("/electronics/phones/accessories", parents=True)
        .mkdir("/electronics/audio/headphones", parents=True)
        .mkdir("/electronics/audio/speakers", parents=True)

        .touch("/electronics/computers/laptops/macbook_pro", "price:1999.99|brand:Apple|ram:16GB|storage:512GB")
        .touch("/electronics/computers/laptops/thinkpad_x1", "price:1499.99|brand:Lenovo|ram:16GB|storage:256GB")
        .touch("/electronics/computers/desktops/imac_24", "price:1299.99|brand:Apple|ram:8GB|storage:256GB")
        .touch("/electronics/phones/smartphones/iphone_15", "price:999.99|brand:Apple|storage:128GB|color:black")
        .touch("/electronics/phones/smartphones/pixel_8", "price:699.99|brand:Google|storage:128GB|color:hazel")
        .touch("/electronics/phones/accessories/case_clear", "price:29.99|brand:Generic|compatible:iphone_15,pixel_8")
        .touch("/electronics/audio/headphones/airpods_pro", "price:249.99|brand:Apple|type:wireless|noise_cancel:yes")
        .touch("/electronics/audio/speakers/homepod_mini", "price:99.99|brand:Apple|type:smart|voice:siri")

        # Home & Garden
        .mkdir("/home/furniture/living_room", parents=True)
        .mkdir("/home/furniture/bedroom", parents=True)
        .mkdir("/home/kitchen/appliances", parents=True)
        .mkdir("/home/kitchen/cookware", parents=True)
        .mkdir("/home/garden/tools", parents=True)
        .mkdir("/home/garden/plants", parents=True)

        .touch("/home/furniture/living_room/sofa_gray", "price:899.99|seats:3|color:gray|material:fabric")
        .touch("/home/furniture/living_room/coffee_table", "price:299.99|shape:rectangular|color:walnut|material:wood")
        .touch("/home/furniture/bedroom/bed_queen", "price:599.99|size:queen|color:white|material:wood")
        .touch("/home/kitchen/appliances/coffee_maker", "price:79.99|brand:Cuisinart|type:drip|cups:12")
        .touch("/home/kitchen/cookware/pan_cast_iron", "price:49.99|brand:Lodge|size:12inch|material:cast_iron")
        .touch("/home/garden/tools/pruning_shears", "price:24.99|brand:Fiskars|type:bypass")
        .touch("/home/garden/plants/succulent_trio", "price:19.99|type:live|light:indirect|water:low")

        # Sports
        .mkdir("/sports/fitness/weights", parents=True)
        .mkdir("/sports/fitness/cardio", parents=True)
        .mkdir("/sports/outdoor/camping", parents=True)
        .mkdir("/sports/outdoor/hiking", parents=True)

        .touch("/sports/fitness/weights/dumbbells_set", "price:199.99|weight:5-50lbs|material:rubber_coated")
        .touch("/sports/fitness/cardio/yoga_mat", "price:29.99|thickness:6mm|color:purple|material:TPE")
        .touch("/sports/outdoor/camping/tent_4person", "price:249.99|capacity:4|season:3|weight:8lbs")
        .touch("/sports/outdoor/hiking/backpack_40L", "price:149.99|capacity:40L|color:navy|waterproof:yes")
    )


if __name__ == "__main__":
    tree = product_catalog()
    print(tree.tree("/"))
