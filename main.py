# github action reference https://github.com/actions/setup-python

import json
from classes.goal_id import GoalID

def main():
    goal_id = GoalID()
    goal_id.process()

    with open("./data/goal_id.json", "w") as external_file:
        external_file.write(json.dumps(goal_id.result))
        external_file.close()

main()