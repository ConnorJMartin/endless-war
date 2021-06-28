
jr_mines = "jr_mines"
cv_mines = "cv_mines"
tt_mines = "tt_mines"
jr_farms = "jr_farms"
og_farms = "og_farms"
ab_farms = "ab_farms"





poi_to_help_responses = {
    help_mine_explaniation: "just spam !mine jackass"
    help_farm_explaniation: "use the !sow and !reap commands idiot"
}

poi_to_help_responses = {
    jr_mines: help_mine_explaniation,
    cv_mines: help_mine_explaniation,
    tt_mines: help_mine_explaniation,
    jr_farms: help_farm_explaniation,
    og_farms: help_farm_explaniation,
    ab_farms: help_farm_explaniation,
}


for key, value in help_responses.items():
    print(f"{key} - {value}\n")


help_responses[jr_mines] = "please use !mine"
help_responses[jr_farms] = "please use !sow and !reap"


for key, value in help_responses.items():
    print(f"{key} - {value}\n")
