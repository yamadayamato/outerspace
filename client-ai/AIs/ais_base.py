#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import copy
from ige import log
from ige.ospace import Const
from ige.ospace import Rules
from ige.ospace import Utils

import ai_tools as tool

class AI(object):
    def __init__(self, client):
        self.client = client
        self.db = client.db
        self.player = client.getPlayer()

        self.data = tool.tool_parseDB(self.client, self.db)

    def economy_manager(self):
        raise NotImplementedError

    def defense_manager(self):
        raise NotImplementedError

    def offense_manager(self):
        raise NotImplementedError

    def research_manager(self):
        raise NotImplementedError

    def diplomacy_manager(self):
        raise NotImplementedError

    def _find_best_planet(self, planet_ids):
        # right now, it's simply the largest one
        max_slots = 0
        largest_planet_id = None
        for planet_id in planet_ids:
            planet = self.db[planet_id]
            if max_slots < planet.plSlots:
                max_slots = planet.plSlots
                largest_planet_id = planet_id
        return largest_planet_id

    def _explore(self, explorer_design_id):
        should_repeat = False
        explorer_fleets = self.data.myFleetsWithDesign.get(explorer_design_id, set())
        for fleet_id in copy.copy(explorer_fleets & self.data.idleFleets):
            max_range = tool.subfleetMaxRange(self.client, self.db, {explorer_design_id:1}, fleet_id)
            nearest = tool.findNearest(self.db, self.db[fleet_id], self.data.unknownSystems, max_range)
            if len(nearest) > 0:
                system_id = nearest[0]
                # send the fleet
                fleet, new_fleet, my_fleets = tool.orderPartFleet(self.client, self.db,
                    {explorer_design_id:1}, True, fleet_id, Const.FLACTION_MOVE, system_id, None)
                self.data.myFleetSheets[fleet_id][explorer_design_id] -= 1
                if self.data.myFleetSheets[fleet_id][explorer_design_id] == 0:
                    del self.data.myFleetSheets[fleet_id][explorer_design_id]
                    explorer_fleets.remove(fleet_id)
                else:
                    should_repeat = True
                self.data.unknownSystems.remove(system_id)
        return should_repeat

    def _colonize_free_systems(self, valid_systems, colony_design_id):
        should_repeat = False
        colony_fleets = self.data.myFleetsWithDesign.get(colony_design_id, set())
        for fleet_id in copy.copy(colony_fleets & self.data.idleFleets):
            max_range = tool.subfleetMaxRange(self.client, self.db, {colony_design_id:1}, fleet_id)
            nearest = tool.findNearest(self.db, self.db[fleet_id], valid_systems, max_range)
            if len(nearest) > 0:
                system_id = nearest[0]
                system = self.db[system_id]
                target_id = self._find_best_planet(system.planets)
                fleet, new_fleet, my_fleets = tool.orderPartFleet(self.client, self.db,
                    {colony_design_id:1}, True, fleet_id, Const.FLACTION_DEPLOY, target_id, colony_design_id)
                self.data.myFleetSheets[fleet_id][colony_design_id] -= 1
                if self.data.myFleetSheets[fleet_id][colony_design_id] == 0:
                    del self.data.myFleetSheets[fleet_id][colony_design_id]
                    colony_fleets.remove(fleet_id)
                else:
                    should_repeat = True
                self.data.freeSystems.remove(system_id)
                valid_systems.remove(system_id)
        return should_repeat

    def run(self):
        self.economy_manager()
        self.defense_manager()
        self.offense_manager()
        self.research_manager()
        self.diplomacy_manager()

