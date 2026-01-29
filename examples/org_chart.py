"""Company organization chart - departments, teams, and people."""

from loopy import Loopy


def org_chart() -> Loopy:
    """
    A company org chart demonstrating hierarchical people management.

    Use cases for LLMs:
    - "Who reports to the VP of Engineering?"
    - "Find all senior engineers"
    - "Move Alice from Platform to ML team"
    - "What's the headcount in Product?"
    - "List everyone in the San Francisco office"
    """
    return (
        Loopy()
        # Executive
        .mkdir("/company/executive", parents=True)
        .touch("/company/executive/ceo_sarah", "name:Sarah Chen|title:CEO|location:SF|joined:2018|email:sarah@acme.com|reports_to:board")
        .touch("/company/executive/cto_mike", "name:Mike Rodriguez|title:CTO|location:SF|joined:2019|email:mike@acme.com|reports_to:ceo_sarah")
        .touch("/company/executive/cfo_lisa", "name:Lisa Park|title:CFO|location:NYC|joined:2020|email:lisa@acme.com|reports_to:ceo_sarah")
        .touch("/company/executive/cpo_james", "name:James Wilson|title:CPO|location:SF|joined:2019|email:james@acme.com|reports_to:ceo_sarah")

        # Engineering
        .mkdir("/company/engineering/platform", parents=True)
        .mkdir("/company/engineering/frontend", parents=True)
        .mkdir("/company/engineering/backend", parents=True)
        .mkdir("/company/engineering/ml", parents=True)
        .mkdir("/company/engineering/devops", parents=True)
        .mkdir("/company/engineering/security", parents=True)

        .touch("/company/engineering/vp_eng_david", "name:David Kim|title:VP Engineering|location:SF|joined:2019|email:david@acme.com|reports_to:cto_mike")

        # Platform team
        .touch("/company/engineering/platform/mgr_alice", "name:Alice Zhang|title:Engineering Manager|location:SF|joined:2020|email:alice@acme.com|reports_to:vp_eng_david")
        .touch("/company/engineering/platform/sr_eng_bob", "name:Bob Smith|title:Senior Engineer|location:SF|joined:2021|email:bob@acme.com|reports_to:mgr_alice|skills:go,kubernetes,postgres")
        .touch("/company/engineering/platform/eng_carol", "name:Carol Davis|title:Software Engineer|location:Remote|joined:2022|email:carol@acme.com|reports_to:mgr_alice|skills:python,aws,terraform")
        .touch("/company/engineering/platform/eng_dan", "name:Dan Lee|title:Software Engineer|location:SF|joined:2023|email:dan@acme.com|reports_to:mgr_alice|skills:rust,linux,networking")

        # Frontend team
        .touch("/company/engineering/frontend/mgr_emma", "name:Emma Johnson|title:Engineering Manager|location:NYC|joined:2020|email:emma@acme.com|reports_to:vp_eng_david")
        .touch("/company/engineering/frontend/sr_eng_frank", "name:Frank Brown|title:Senior Engineer|location:NYC|joined:2021|email:frank@acme.com|reports_to:mgr_emma|skills:react,typescript,graphql")
        .touch("/company/engineering/frontend/eng_grace", "name:Grace Liu|title:Software Engineer|location:Remote|joined:2022|email:grace@acme.com|reports_to:mgr_emma|skills:vue,css,accessibility")
        .touch("/company/engineering/frontend/eng_henry", "name:Henry Wang|title:Software Engineer|location:NYC|joined:2023|email:henry@acme.com|reports_to:mgr_emma|skills:react,nextjs,testing")

        # Backend team
        .touch("/company/engineering/backend/mgr_ivan", "name:Ivan Petrov|title:Engineering Manager|location:SF|joined:2020|email:ivan@acme.com|reports_to:vp_eng_david")
        .touch("/company/engineering/backend/sr_eng_julia", "name:Julia Martinez|title:Senior Engineer|location:SF|joined:2020|email:julia@acme.com|reports_to:mgr_ivan|skills:java,spring,kafka")
        .touch("/company/engineering/backend/eng_kevin", "name:Kevin O'Brien|title:Software Engineer|location:Remote|joined:2022|email:kevin@acme.com|reports_to:mgr_ivan|skills:python,django,redis")
        .touch("/company/engineering/backend/eng_linda", "name:Linda Chen|title:Software Engineer|location:SF|joined:2023|email:linda@acme.com|reports_to:mgr_ivan|skills:go,grpc,mongodb")

        # ML team
        .touch("/company/engineering/ml/mgr_nina", "name:Nina Patel|title:ML Engineering Manager|location:SF|joined:2021|email:nina@acme.com|reports_to:vp_eng_david")
        .touch("/company/engineering/ml/sr_ml_omar", "name:Omar Hassan|title:Senior ML Engineer|location:SF|joined:2021|email:omar@acme.com|reports_to:mgr_nina|skills:pytorch,transformers,mlops")
        .touch("/company/engineering/ml/ml_eng_priya", "name:Priya Sharma|title:ML Engineer|location:Remote|joined:2022|email:priya@acme.com|reports_to:mgr_nina|skills:tensorflow,computer_vision,aws_sagemaker")
        .touch("/company/engineering/ml/data_sci_quinn", "name:Quinn Taylor|title:Data Scientist|location:SF|joined:2023|email:quinn@acme.com|reports_to:mgr_nina|skills:python,statistics,experimentation")

        # DevOps team
        .touch("/company/engineering/devops/mgr_raj", "name:Raj Gupta|title:DevOps Manager|location:SF|joined:2020|email:raj@acme.com|reports_to:vp_eng_david")
        .touch("/company/engineering/devops/sr_sre_sam", "name:Sam Jackson|title:Senior SRE|location:Remote|joined:2021|email:sam@acme.com|reports_to:mgr_raj|skills:kubernetes,prometheus,incident_response")
        .touch("/company/engineering/devops/devops_tina", "name:Tina Wu|title:DevOps Engineer|location:SF|joined:2022|email:tina@acme.com|reports_to:mgr_raj|skills:terraform,ansible,ci_cd")

        # Security team
        .touch("/company/engineering/security/mgr_uma", "name:Uma Krishnan|title:Security Manager|location:NYC|joined:2021|email:uma@acme.com|reports_to:vp_eng_david")
        .touch("/company/engineering/security/sec_eng_victor", "name:Victor Reyes|title:Security Engineer|location:NYC|joined:2022|email:victor@acme.com|reports_to:mgr_uma|skills:penetration_testing,compliance,soc2")

        # Product
        .mkdir("/company/product/growth", parents=True)
        .mkdir("/company/product/core", parents=True)
        .mkdir("/company/product/enterprise", parents=True)

        .touch("/company/product/vp_prod_wendy", "name:Wendy Brooks|title:VP Product|location:SF|joined:2020|email:wendy@acme.com|reports_to:cpo_james")
        .touch("/company/product/growth/pm_xander", "name:Xander Cole|title:Senior PM|location:SF|joined:2021|email:xander@acme.com|reports_to:vp_prod_wendy|focus:activation,retention")
        .touch("/company/product/core/pm_yuki", "name:Yuki Tanaka|title:Product Manager|location:Remote|joined:2022|email:yuki@acme.com|reports_to:vp_prod_wendy|focus:core_features")
        .touch("/company/product/enterprise/pm_zoe", "name:Zoe Adams|title:Product Manager|location:NYC|joined:2022|email:zoe@acme.com|reports_to:vp_prod_wendy|focus:enterprise_features,sso")

        # Design
        .mkdir("/company/design/product_design", parents=True)
        .mkdir("/company/design/brand", parents=True)
        .mkdir("/company/design/research", parents=True)

        .touch("/company/design/head_design_amy", "name:Amy Foster|title:Head of Design|location:SF|joined:2020|email:amy@acme.com|reports_to:cpo_james")
        .touch("/company/design/product_design/sr_des_ben", "name:Ben Harper|title:Senior Product Designer|location:SF|joined:2021|email:ben@acme.com|reports_to:head_design_amy|tools:figma,protopie")
        .touch("/company/design/product_design/des_claire", "name:Claire Mitchell|title:Product Designer|location:Remote|joined:2022|email:claire@acme.com|reports_to:head_design_amy|tools:figma,framer")
        .touch("/company/design/brand/brand_des_derek", "name:Derek Stone|title:Brand Designer|location:NYC|joined:2022|email:derek@acme.com|reports_to:head_design_amy|tools:illustrator,after_effects")
        .touch("/company/design/research/ux_res_elena", "name:Elena Voss|title:UX Researcher|location:SF|joined:2023|email:elena@acme.com|reports_to:head_design_amy|methods:interviews,usability_testing")

        # Finance
        .mkdir("/company/finance/accounting", parents=True)
        .mkdir("/company/finance/fp_and_a", parents=True)

        .touch("/company/finance/controller_fred", "name:Fred Marshall|title:Controller|location:NYC|joined:2021|email:fred@acme.com|reports_to:cfo_lisa")
        .touch("/company/finance/accounting/acct_gloria", "name:Gloria Ruiz|title:Senior Accountant|location:NYC|joined:2022|email:gloria@acme.com|reports_to:controller_fred")
        .touch("/company/finance/fp_and_a/analyst_hiro", "name:Hiro Nakamura|title:FP&A Analyst|location:NYC|joined:2023|email:hiro@acme.com|reports_to:cfo_lisa")

        # People/HR
        .mkdir("/company/people/recruiting", parents=True)
        .mkdir("/company/people/people_ops", parents=True)

        .touch("/company/people/head_people_iris", "name:Iris Chang|title:Head of People|location:SF|joined:2020|email:iris@acme.com|reports_to:ceo_sarah")
        .touch("/company/people/recruiting/recruiter_jack", "name:Jack Rivera|title:Technical Recruiter|location:SF|joined:2021|email:jack@acme.com|reports_to:head_people_iris|focus:engineering")
        .touch("/company/people/recruiting/recruiter_kate", "name:Kate Murphy|title:Recruiter|location:Remote|joined:2022|email:kate@acme.com|reports_to:head_people_iris|focus:go_to_market")
        .touch("/company/people/people_ops/hr_leo", "name:Leo Santos|title:People Operations|location:SF|joined:2022|email:leo@acme.com|reports_to:head_people_iris")

        # Locations (cross-reference)
        .mkdir("/locations/sf", parents=True)
        .mkdir("/locations/nyc", parents=True)
        .mkdir("/locations/remote", parents=True)

        .touch("/locations/sf/address", "123 Market St, San Francisco, CA 94105|capacity:150|opened:2019")
        .touch("/locations/nyc/address", "456 Broadway, New York, NY 10013|capacity:50|opened:2021")
        .touch("/locations/remote/policy", "Fully remote employees across US timezones|equipment_stipend:$1000|coworking_budget:$200/mo")
    )


if __name__ == "__main__":
    tree = org_chart()
    print(tree.tree("/company/engineering"))
