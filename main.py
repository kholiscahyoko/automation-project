# github action reference https://github.com/actions/setup-python

import json
from classes.goal_id import GoalID
from classes.tempo_co import TempoCo

def main():
    # #goal indonesia
    # goal_id = GoalID()
    # goal_id.process()
    #
    # with open("./data/goal_id.json", "w") as external_file:
    #     external_file.write(json.dumps(goal_id.result))
    #     external_file.close()

    #tempo.co
    tempo_co = TempoCo()
    tempo_co.process()

    with open("./data/tempo_co.json", "w") as external_file:
        external_file.write(json.dumps(tempo_co.result))
        external_file.close()

main()