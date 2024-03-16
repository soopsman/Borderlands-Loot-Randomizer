from unrealsdk import Log, FindObject, GetEngine  #type: ignore
from unrealsdk import RunHook, RemoveHook, UObject, UFunction, FStruct #type: ignore

from .defines import Tag, construct_object
from .locations import Location, Dropper, Behavior, MapDropper, Interactive
from .enemies import Enemy, Pawn
from .items import ItemPool

from typing import Optional, Sequence, Set


class Leviathan(MapDropper):
    def __init__(self) -> None:
        super().__init__("Orchid_WormBelly_P")

    def entered_map(self) -> None:
        def hook(caller: UObject, function: UFunction, params: FStruct) -> bool:
            if UObject.PathName(caller.MissionObjective) != "GD_Orchid_Plot_Mission09.M_Orchid_PlotMission09:KillBossWorm":
                return True

            pawn = GetEngine().GetCurrentWorldInfo().PawnList
            while pawn:
                if pawn.AIClass and pawn.AIClass.Name == "CharacterClass_Orchid_BossWorm":
                    break
                pawn = pawn.NextPawn

            spawner = construct_object("Behavior_SpawnLootAroundPoint")

            spawner.ItemPools = self.location.pools
            spawner.SpawnVelocity = (-400, -1800, -400)
            spawner.SpawnVelocityRelativeTo = 1
            spawner.CustomLocation = ((1200, -66000, 3000), None, "")
            spawner.CircularScatterRadius = 200

            self.location.item.prepare()
            spawner.ApplyBehaviorToContext(pawn, (), None, None, None, ())
            self.location.item.revert()

            return True

        RunHook("WillowGame.Behavior_UpdateMissionObjective.ApplyBehaviorToContext", f"LootRandomizer.{id(self)}", hook)
        
    def exited_map(self) -> None:
        RemoveHook("WillowGame.Behavior_UpdateMissionObjective.ApplyBehaviorToContext", f"LootRandomizer.{id(self)}")


class MonsterTruck(MapDropper):
    def __init__(self) -> None:
        super().__init__("Iris_Hub2_P")

    def entered_map(self) -> None:
        def hook(caller: UObject, function: UFunction, params: FStruct) -> bool:
            if not (caller.VehicleDef and caller.VehicleDef.Name == "Class_MonsterTruck_AIOnly"):
                return True

            spawner = construct_object("Behavior_SpawnLootAroundPoint")
            spawner.ItemPools = self.location.pools

            self.location.item.prepare()
            spawner.ApplyBehaviorToContext(caller, (), None, None, None, ())
            self.location.item.revert()

        RunHook("Engine.Pawn.Died", f"LootRandomizer.{id(self)}", hook)

    def exited_map(self) -> None:
        RemoveHook("Engine.Pawn.Died", f"LootRandomizer.{id(self)}")


_doctorsorders_midgets: Set[str] = set()

def _spawn_midget(caller: UObject, function: UFunction, params: FStruct) -> bool:
    if UObject.PathName(caller) == "GD_Balance_Treasure.InteractiveObjectsTrap.MidgetHyperion.InteractiveObj_CardboardBox_MidgetHyperion:BehaviorProviderDefinition_1.Behavior_SpawnFromPopulationSystem_5":
        _doctorsorders_midgets.add(UObject.PathName(params.SpawnedActor))
    return True

class Midget(Pawn):
    def should_inject(self, pawn: UObject) -> bool:
        return (
            UObject.PathName(pawn) not in _doctorsorders_midgets and
            UObject.PathName(pawn.MySpawnPoint) != "OldDust_Mission_Side.TheWorld:PersistentLevel.WillowPopulationPoint_26"
        )

class DoctorsOrdersMidget(Pawn):
    def should_inject(self, pawn: UObject) -> None:
        return UObject.PathName(pawn) in _doctorsorders_midgets

class SpaceCowboyMidget(Pawn):
    def should_inject(self, pawn: UObject) -> None:
        return UObject.PathName(pawn.MySpawnPoint) == "OldDust_Mission_Side.TheWorld:PersistentLevel.WillowPopulationPoint_26"

class DoctorsOrdersMidgetRegistry(MapDropper):
    def __init__(self) -> None:
        super().__init__("PandoraPark_P")

    def entered_map(self) -> None:
        _doctorsorders_midgets.clear()
        RunHook("WillowGame.Behavior_SpawnFromPopulationSystem.PublishBehaviorOutput", f"LootRandomizer.{id(self)}", _spawn_midget)

    def exited_map(self) -> None:
        _doctorsorders_midgets.clear()
        RemoveHook("WillowGame.Behavior_SpawnFromPopulationSystem.PublishBehaviorOutput", f"LootRandomizer.{id(self)}")


class HaderaxChest(Interactive):
    def inject(self, interactive: UObject) -> None:
        pools = self.prepare_pools()
        
        money = FindObject("ItemPoolDefinition", "GD_Itempools.AmmoAndResourcePools.Pool_Money_1_BIG")
        pool = pools[0] if pools else money

        for loot in interactive.Loot:
            loot.ItemAttachments[0].ItemPool = pool
            for index in (1, 2, 3, 8, 9, 10, 11):
                loot.ItemAttachments[index].ItemPool = money


class DigiEnemy(Enemy):
    fallback: str

    _fallback_enemy: Optional[Enemy] = None
    _item: Optional[ItemPool] = None

    def __init__(
        self,
        name: str,
        *droppers: Dropper,
        fallback: str,
        tags: Tag = Tag(0),
        rarities: Optional[Sequence[int]] = None
    ) -> None:
        self.fallback = fallback
        super().__init__(name, *droppers, tags=tags, rarities=rarities)

    @property
    def fallback_enemy(self) -> Enemy:
        if not self._fallback_enemy:
            for enemy in Enemies:
                if enemy.name == self.fallback:
                    self._fallback_enemy = enemy
                    break
        return self._fallback_enemy

    @property
    def item(self) -> Optional[ItemPool]:
        return self._item if self._item else self.fallback_enemy.item

    @item.setter
    def item(self, item: ItemPool) -> None:
        self._item = item

    @property
    def hint_pool(self) -> UObject: #ItemPoolDefinition
        return super().hint_pool if self._item else self.fallback_enemy.hint_pool


Enemies = (
    Enemy("Knuckle Dragger", Pawn("PawnBalance_PrimalBeast_KnuckleDragger")),
    Enemy("Midgemong", Pawn("PawnBalance_PrimalBeast_Warmong")),
    Enemy("Boom", Pawn("PawnBalance_BoomBoom")),
    Enemy("Bewm", Pawn("PawnBalance_Boom")),
    Enemy("Captain Flynt", Pawn("PawnBalance_Flynt"), tags=Tag.SlowEnemy),
    Enemy("Savage Lee", Pawn("PawnBalance_SavageLee")),
    Enemy("Doc Mercy", Pawn("PawnBalance_MrMercy")),
    Enemy("Assassin Wot", Pawn("PawnBalance_Assassin1")),
    Enemy("Assassin Oney", Pawn("PawnBalance_Assassin2")),
    Enemy("Assassin Reeth", Pawn("PawnBalance_Assassin3"), tags=Tag.SlowEnemy),
    Enemy("Assassin Rouf", Pawn("PawnBalance_Assassin4"), tags=Tag.SlowEnemy),
    Enemy("Boll", Pawn("PawnBalance_Boll")),
    Enemy("Scorch", Pawn("PawnBalance_SpiderantScorch")),
    Enemy("Incinerator Clayton", Pawn("PawnBalance_IncineratorVanya_Combat"), tags=Tag.SlowEnemy),
    Enemy("Shirtless Man", Pawn("PawnBalance_ShirtlessMan"), mission="Too Close For Missiles"),
    Enemy("The Black Queen", Pawn("PawnBalance_SpiderantBlackQueen"), tags=Tag.SlowEnemy|Tag.RareEnemy),
    Enemy("Bad Maw", Pawn("PawnBalance_BadMaw")),
    Enemy("Mad Mike", Pawn("PawnBalance_MadMike"), tags=Tag.SlowEnemy),
    Enemy("Loader #1340",
        Pawn("PawnBalance_Constructor_1340"),
        Pawn("PawnBalance_LoaderWAR_1340"),
    mission="Out of Body Experience (Turn in Marcus)"),
    Enemy("Lee", Pawn("PawnBalance_Lee")),
    Enemy("Dan", Pawn("PawnBalance_Dan")),
    Enemy("Ralph", Pawn("PawnBalance_Ralph")),
    Enemy("Mick", Pawn("PawnBalance_Mick")),
    Enemy("Flinter", Pawn("PawnBalance_RatEasterEgg")),
    Enemy("Wilhelm", Pawn("PawnBalance_Willhelm")),
    Enemy("Mutated Badass Varkid", Pawn("PawnBalance_BugMorphBadass_Mutated"), mission="Mighty Morphin'"),
    Enemy("Madame Von Bartlesby", Pawn("PawnBalance_SirReginald")),
    Enemy("Flesh-Stick", Pawn("PawnBalance_FleshStick"), mission="You Are Cordially Invited: RSVP"),
    Enemy("Prospector Zeke", Pawn("PawnBalance_Prospector"), tags=Tag.SlowEnemy),
    Enemy("Mobley", Pawn("PawnBalance_Mobley")),
    Enemy("Gettle", Pawn("PawnBalance_Gettle")),
    Enemy("Badass Creeper", Pawn("PawnBalance_CreeperBadass"), tags=Tag.SlowEnemy),
    Enemy("Henry", Pawn("PawnBalance_Henry")),
    Enemy("Requisition Officer", Pawn("PawnBalance_RequisitionOfficer"), mission="The Overlooked: Medicine Man"),
    Enemy("Old Slappy", Pawn("PawnBalance_Slappy")),
    Enemy("Bagman", Pawn("PawnBalance_Leprechaun"), mission="Clan War: End of the Rainbow"),
    Enemy("Mick Zaford", Pawn("PawnBalance_MickZaford_Combat")),
    Enemy("Tector Hodunk", Pawn("PawnBalance_TectorHodunk_Combat")),
    Enemy("Blue", Pawn("PawnBalance_Blue")),
    Enemy("Daisy", Pawn("BD_Daisy"), mission="Poetic License"),
    Enemy("Sinkhole", Pawn("PawnBalance_Stalker_SwallowedWhole")),
    Enemy("Shorty", Pawn("PawnBalance_Midge")),
    Enemy("Laney White", Pawn("PawnBalance_Laney")),
    Enemy("Smash-Head", Pawn("PawnBalance_SmashHead"), tags=Tag.SlowEnemy),
    Enemy("Rakkman", Pawn("PawnBalance_RakkMan"), tags=Tag.SlowEnemy),
    Enemy("Tumbaa", Pawn("PawnBalance_Tumbaa"), tags=Tag.RareEnemy),
    Enemy("Pimon", Pawn("PawnBalance_Stalker_Simon"), tags=Tag.RareEnemy),
    Enemy("Son of Mothrakk", Pawn("PawnBalance_SonMothrakk"), tags=Tag.SlowEnemy, rarities=(100,)),
    Enemy("Muscles", Pawn("PawnBalance_Bruiser_Muscles"), tags=Tag.VeryRareEnemy),
    Enemy("The Sheriff of Lynchwood", Pawn("PawnBalance_Sheriff")),
    Enemy("Deputy Winger", Pawn("PawnBalance_Deputy")),
    Enemy("Mad Dog", Pawn("PawnBalance_MadDog"), tags=Tag.SlowEnemy),
    Enemy("McNally", Pawn("PawnBalance_McNally")),
    Enemy("Foreman Rusty", Pawn("PawnBalance_Foreman")),
    Enemy("BNK-3R",
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_4"),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_0", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_1", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_2", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_3", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_5", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_6", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_7", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_8", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_9", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_10", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_11", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_12", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_13", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_14", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_15", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_16", inject=False),
        Behavior("GD_HyperionBunkerBoss.Character.AIDef_BunkerBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_17", inject=False),
    tags=Tag.SlowEnemy),
    Enemy("Jim Kepler", Pawn("BD_BFF_Jim"), mission="BFFs"),
    Enemy("Dukino's Mom", Pawn("PawnBalance_Skagzilla")),
    Enemy("Donkey Mong", Pawn("PawnBalance_PrimalBeast_DonkeyMong"), tags=Tag.RareEnemy),
    Enemy("King Mong", Pawn("PawnBalance_PrimalBeast_KingMong"), tags=Tag.RareEnemy),
    Enemy("Geary", Pawn("PawnBalance_Smagal"), tags=Tag.SlowEnemy),
    Enemy("Mortar", Pawn("PawnBalance_Mortar")),
    Enemy("Hunter Hellquist", Pawn("PawnBalance_DJHyperion")),
    Enemy("Spycho", Pawn("PawnBalance_MonsterMash1"), tags=Tag.SlowEnemy),
    Enemy("Bone Head 2.0", Pawn("PawnBalance_BoneHead2")),
    Enemy("Saturn", Pawn("PawnBalance_LoaderGiant")),
    Enemy("The Warrior",
        # TODO fix spawnitems vectors
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_16.Behavior_SpawnItems_6"),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_31.Behavior_SpawnItems_6"),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_59.Behavior_SpawnItems_6"),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_12.Behavior_SpawnItems_6", inject=False),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_14.Behavior_SpawnItems_6", inject=False),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_15.Behavior_SpawnItems_6", inject=False),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_56.Behavior_SpawnItems_6", inject=False),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_57.Behavior_SpawnItems_6", inject=False),
        Behavior("Boss_Volcano_Combat_Monster.TheWorld:PersistentLevel.Main_Sequence.SeqAct_ApplyBehavior_58.Behavior_SpawnItems_6", inject=False),
        Behavior("GD_FinalBoss.Character.AIDef_FinalBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_12", inject=False),
        Behavior("GD_FinalBoss.Character.AIDef_FinalBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_13", inject=False),
        Behavior("GD_FinalBoss.Character.AIDef_FinalBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_14", inject=False),
        Behavior("GD_FinalBoss.Character.AIDef_FinalBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_15", inject=False),
        Behavior("GD_FinalBoss.Character.AIDef_FinalBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_16", inject=False),
        Behavior("GD_FinalBoss.Character.AIDef_FinalBoss:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_17", inject=False),
    tags=Tag.SlowEnemy),
    Enemy("Terramorphous the Invincible",
        # TODO: test pawn for disappearing loot; maybe switch to behavior
        Pawn("PawnBalance_ThresherRaid"),
        Behavior("GD_ThresherShared.Anims.Anim_Raid_Death1:BehaviorProviderDefinition_29.Behavior_SpawnItems_46", inject=False),
        Behavior("GD_ThresherShared.Anims.Anim_Raid_Death1:BehaviorProviderDefinition_29.Behavior_SpawnItems_47", inject=False),
    tags=Tag.RaidEnemy),

    Enemy("Loot Midget",
        Midget("PawnBalance_Jimmy"),
        Midget("PawnBalance_LootMidget_CombatEngineer"),
        Midget("PawnBalance_LootMidget_Engineer"),
        Midget("PawnBalance_LootMidget_LoaderGUN"),
        Midget("PawnBalance_LootMidget_LoaderJET"),
        Midget("PawnBalance_LootMidget_LoaderWAR"),
        Midget("PawnBalance_LootMidget_Marauder"),
        Midget("PawnBalance_LootMidget_Goliath"),
        Midget("PawnBalance_LootMidget_Nomad"),
        Midget("PawnBalance_LootMidget_Psycho"),
        Midget("PawnBalance_LootMidget_Rat"),
        DoctorsOrdersMidgetRegistry(),
    tags=Tag.RareEnemy),
    Enemy("Loot Midget (Doctor's Orders)",
        DoctorsOrdersMidget("PawnBalance_Jimmy"),
        DoctorsOrdersMidget("PawnBalance_LootMidget_CombatEngineer"),
        DoctorsOrdersMidget("PawnBalance_LootMidget_Engineer"),
        DoctorsOrdersMidget("PawnBalance_LootMidget_LoaderGUN"),
        DoctorsOrdersMidget("PawnBalance_LootMidget_LoaderJET"),
        DoctorsOrdersMidget("PawnBalance_LootMidget_LoaderWAR"),
        DoctorsOrdersMidgetRegistry(),
    mission="Doctor's Orders"),
    Enemy("Chubby/Tubby",
        Pawn("PawnBalance_BugMorphChubby"),
        Pawn("PawnBalance_MidgetChubby"),
        Pawn("PawnBalance_RakkChubby"),
        Pawn("PawnBalance_SkagChubby"),
        Pawn("PawnBalance_SpiderantChubby"),
        Pawn("PawnBalance_StalkerChubby"),
        Pawn("PawnBalance_SkagChubby_Orchid"),
        Pawn("PawnBalance_SpiderantChubby_Orchid"),
        Pawn("PawnBalance_Orchid_StalkerChubby"),
        Pawn("PawnBalance_SkeletonChubby"),
    tags=Tag.VeryRareEnemy),
    Enemy("GOD-liath",
        Pawn("PawnBalance_Goliath", transform=5),
        Pawn("PawnBalance_GoliathBadass", transform=5),
        Pawn("PawnBalance_GoliathCorrosive", transform=5),
        Pawn("PawnBalance_DiggerGoliath", transform=5),
        Pawn("PawnBalance_GoliathBlaster", transform=5),
        Pawn("PawnBalance_GoliathLootGoon", transform=5),
        Pawn("PawnBalance_LootMidget_Goliath", transform=5),
        Pawn("PawnBalance_MidgetGoliath", transform=5), # Stops at 5 ("Giant Midget of Death")
        # Pawn("PawnBalance_GoliathTurret", transform=3), # Stops at 3 ("Ultimate Badass Heavy")
        Pawn("Iris_PawnBalance_ArenaGoliath", transform=5),
        Pawn("PawnBalance_InfectedGoliath", transform=5),
        Pawn("PawnBalance_Infected_Badass_Goliath", transform=5),
        Pawn("PawnBalance_Infected_Gargantuan_Goliath", transform=5),
        Pawn("PawnBalance_GoliathSnow", transform=5),
        Pawn("PawnBalance_GoliathBride", transform=5),
        Pawn("PawnBalance_GoliathBrideRaid", transform=5),
        Pawn("PawnBalance_GoliathGroom", transform=5),
        Pawn("PawnBalance_GoliathGroomRaid", transform=5),
    tags=Tag.EvolvedEnemy),
    Enemy("Ultimate Badass Varkid", Pawn("PawnBalance_BugMorphUltimateBadass"), tags=Tag.EvolvedEnemy|Tag.VeryRareEnemy),
    Enemy("Vermivorous the Invincible", Pawn("PawnBalance_BugMorphRaid"), tags=Tag.EvolvedEnemy|Tag.RaidEnemy|Tag.VeryRareEnemy),

    Enemy("Tinkles", Pawn("PawnBalance_Orchid_StalkerPet"), tags=Tag.PiratesBooty),
    Enemy("The Big Sleep", Pawn("PawnBalance_Orchid_BigSleep"), tags=Tag.PiratesBooty),
    Enemy("Sandman", Pawn("PawnBalance_Orchid_Sandman_Solo"), tags=Tag.PiratesBooty),
    Enemy("Grendel", Pawn("PawnBalance_Orchid_Grendel"), tags=Tag.PiratesBooty),
    Enemy("Benny the Booster", Pawn("PawnBalance_Orchid_Deserter1"), tags=Tag.PiratesBooty),
    Enemy("Deckhand", Pawn("PawnBalance_Orchid_Deserter2"), tags=Tag.PiratesBooty),
    Enemy("Toothless Terry", Pawn("PawnBalance_Orchid_Deserter3"), mission="Just Desserts for Desert Deserters", tags=Tag.SlowEnemy),
    Enemy("P3RV-E", Pawn("PawnBalance_Orchid_Pervbot"), tags=Tag.PiratesBooty|Tag.SlowEnemy),
    Enemy("H3RL-E", Pawn("PawnBalance_Orchid_LoaderBoss"), tags=Tag.PiratesBooty|Tag.SlowEnemy),
    Enemy("DJ Tanner", Pawn("PawnBalance_Orchid_PirateRadioGuy"), tags=Tag.PiratesBooty|Tag.SlowEnemy),
    Enemy("Mr. Bubbles", Pawn("PawnBalance_Orchid_Bubbles"), tags=Tag.PiratesBooty|Tag.RareEnemy),
    Enemy("Lil' Sis", Behavior("GD_Orchid_LittleSis.Character.AIDef_Orchid_LittleSis:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_85"), tags=Tag.PiratesBooty|Tag.RareEnemy),
    Enemy("Lieutenant White", Pawn("PawnBalance_Orchid_PirateHenchman"), mission="Treasure of the Sands"),
    Enemy("Lieutenant Hoffman", Pawn("PawnBalance_Orchid_PirateHenchman2"), mission="Treasure of the Sands"),
    Enemy("Captain Scarlett", Behavior("GD_Orchid_PirateQueen_Combat.Animation.Anim_Farewell:BehaviorProviderDefinition_0.Behavior_SpawnItems_10"), mission="Treasure of the Sands"),
    Enemy("Leviathan", Leviathan(), mission="Treasure of the Sands", tags=Tag.SlowEnemy),
    Enemy("Hyperius the Invincible",
        Pawn("PawnBalance_Orchid_RaidEngineer"),
        Behavior("GD_Orchid_RaidEngineer.Death.BodyDeath_Orchid_RaidEngineer:BehaviorProviderDefinition_6.Behavior_SpawnItems_203", inject=False),
        Behavior("GD_Orchid_RaidEngineer.Death.BodyDeath_Orchid_RaidEngineer:BehaviorProviderDefinition_6.Behavior_SpawnItems_204", inject=False),
    tags=Tag.PiratesBooty|Tag.RaidEnemy),
    Enemy("Master Gee the Invincible",
        Pawn("PawnBalance_Orchid_RaidShaman"),
        Behavior("GD_Orchid_RaidShaman.Character.AIDef_Orchid_RaidShaman:AIBehaviorProviderDefinition_0.Behavior_SpawnItems_102", inject=False),
        Behavior("GD_Orchid_RaidShaman.Character.AIDef_Orchid_RaidShaman:AIBehaviorProviderDefinition_0.Behavior_SpawnItems_103", inject=False),
        Behavior("GD_Orchid_RaidShaman.Character.AIDef_Orchid_RaidShaman:AIBehaviorProviderDefinition_0.Behavior_SpawnItems_257", inject=False),
        Behavior("Transient.Behavior_SpawnItems_Orchid_MasterGeeDeath", inject=False),
    tags=Tag.PiratesBooty|Tag.RaidEnemy|Tag.SlowEnemy),

    Enemy("Gladiator Goliath", Pawn("Iris_PawnBalance_ArenaGoliath", evolved=5), mission="Tier 2 Battle: Appetite for Destruction"),
    Enemy("Pete's Burner",
        Pawn("Iris_PawnBalance_BikerMidget"),
        Pawn("Iris_PawnBalance_BikerBruiser"),
        Pawn("Iris_PawnBalance_Biker"),
        Pawn("Iris_PawnBalance_BikerBadass"),
        Pawn("Iris_PawnBalance_BigBiker"),
        Pawn("Iris_PawnBalance_BigBikerBadass"),
    tags=Tag.CampaignOfCarnage|Tag.MobFarm),
    Enemy("Hamhock the Ham", Pawn("Iris_PawnBalance_BB_Hamlock"), mission="Mother-Lover (Turn in Scooter)"),
    Enemy("Anonymous Troll Face", Pawn("Iris_PawnBalance_SayFaceTroll"), mission="Say That To My Face"),
    Enemy("Sully the Stabber", Pawn("Iris_PawnBalance_SullyTheStabber"), mission="Number One Fan"),
    Enemy("Motor Momma", Pawn("Iris_PawnBalance_MotorMama"), tags=Tag.CampaignOfCarnage|Tag.SlowEnemy),
    Enemy("The Monster Truck", MonsterTruck(), mission="Monster Hunter"),
    Enemy("Chubby Rakk (Gas Guzzlers)", Pawn("Iris_PawnBalance_RakkChubby"), mission="Gas Guzzlers (Turn in Hammerlock)"),
    Enemy("BuffGamer G", Pawn("Iris_PawnBalance_BB_JohnnyAbs"), mission="Matter Of Taste"),
    Enemy("Game Critic Extraordinaire", Pawn("Iris_PawnBalance_BB_TonyGlutes"), mission="Matter Of Taste"),
    Enemy("Piston/Badassasarus Rex",
        Pawn("Iris_PawnBalance_Truckasaurus"),
        Pawn("Iris_PawnBalance_PistonBoss"),
        Pawn("Iris_PawnBalance_Truckasaurus_Runable"),
    tags=Tag.CampaignOfCarnage|Tag.SlowEnemy),
    Enemy("Pyro Pete the Invincible",
        Pawn("Iris_PawnBalance_RaidPete"),
        Behavior("GD_Iris_Raid_PyroPete.Death.BodyDeath_Iris_Raid_PyroPete:BehaviorProviderDefinition_6.Behavior_SpawnItems_5", inject=False),
        Behavior("GD_Iris_Raid_PyroPete.Death.BodyDeath_Iris_Raid_PyroPete:BehaviorProviderDefinition_6.Behavior_SpawnItems_6", inject=False),
        Behavior("GD_Iris_Raid_PyroPete.Death.BodyDeath_Iris_Raid_PyroPete:BehaviorProviderDefinition_6.Behavior_SpawnItems_7", inject=False),
        Behavior("GD_Iris_Raid_PyroPete.Death.BodyDeath_Iris_Raid_PyroPete:BehaviorProviderDefinition_6.Behavior_SpawnItems_8", inject=False),
        Behavior("GD_Iris_Raid_PyroPete.Death.BodyDeath_Iris_Raid_PyroPete:BehaviorProviderDefinition_6.Behavior_SpawnItems_9", inject=False),
    tags=Tag.CampaignOfCarnage|Tag.RaidEnemy),

    Enemy("Bulstoss", Pawn("PawnBalance_Sage_AcquiredTaste_Creature"), tags=Tag.HammerlocksHunt|Tag.SlowEnemy),
    Enemy("Der Monstrositat", Pawn("PawnBalance_Sage_BorokCage_Creature"), mission="Still Just a Borok in a Cage"),
    Enemy("Arizona", Pawn("PawnBalance_DrifterNamed"), tags=Tag.HammerlocksHunt|Tag.SlowEnemy),
    Enemy("The Bulwark", Pawn("Balance_Sage_SM_PallingAround_Creature"), tags=Tag.HammerlocksHunt|Tag.SlowEnemy),
    Enemy("Rakkanoth", Pawn("PawnBalance_Sage_DahliaMurder_Creature"), mission="The Rakk Dahlia Murder"),
    Enemy("Woundspike", Pawn("PawnBalance_Sage_Ep4_Creature"), tags=Tag.HammerlocksHunt|Tag.SlowEnemy),
    Enemy("Dribbles", Pawn("PawnBalance_Sage_FollowGlow_Creature"), tags=Tag.HammerlocksHunt),
    Enemy("Rouge",
        Pawn("PawnBalance_Sage_BigFeet_Creature"),
        Behavior("GD_Sage_SM_BigFeetData.Creature.Character.BodyDeath_BigFeetCrystalisk:BehaviorProviderDefinition_6.Behavior_SpawnItems_115", inject=False),
        Behavior("GD_Sage_SM_BigFeetData.Creature.Character.BodyDeath_BigFeetCrystalisk:BehaviorProviderDefinition_6.Behavior_SpawnItems_114", inject=False),
        Behavior("GD_Sage_SM_BigFeetData.Creature.Character.BodyDeath_BigFeetCrystalisk:BehaviorProviderDefinition_6.Behavior_SpawnItems_116", inject=False),
        Behavior("GD_Sage_SM_BigFeetData.Creature.Character.BodyDeath_BigFeetCrystalisk:BehaviorProviderDefinition_6.Behavior_SpawnItems_117", inject=False),
        Behavior("GD_Sage_SM_BigFeetData.Creature.Character.BodyDeath_BigFeetCrystalisk:BehaviorProviderDefinition_6.Behavior_SpawnItems_118", inject=False),
        Behavior("GD_Sage_SM_BigFeetData.Creature.Character.BodyDeath_BigFeetCrystalisk:BehaviorProviderDefinition_6.Behavior_SpawnItems_119", inject=False),
    tags=Tag.HammerlocksHunt|Tag.SlowEnemy),
    Enemy("Bloodtail", Pawn("PawnBalance_Sage_NowYouSeeIt_Creature"), tags=Tag.HammerlocksHunt|Tag.SlowEnemy),
    Enemy("Jackenstein", Pawn("PawnBalance_Sage_FinalBoss"), tags=Tag.HammerlocksHunt|Tag.SlowEnemy),
    Enemy("Voracidous the Invincible",
        Pawn("Balance_Sage_Raid_Beast"),
        Behavior("GD_Sage_Raid_Beast.Character.DeathDef_Sage_Raid_Beast:BehaviorProviderDefinition_0.Behavior_SpawnItems_0", inject=False),
        Behavior("GD_Sage_Raid_Beast.Character.DeathDef_Sage_Raid_Beast:BehaviorProviderDefinition_0.Behavior_SpawnItems_1", inject=False),
        Behavior("GD_Sage_Raid_Beast.Character.DeathDef_Sage_Raid_Beast:BehaviorProviderDefinition_0.Behavior_SpawnItems_2", inject=False),
    tags=Tag.HammerlocksHunt|Tag.RaidEnemy|Tag.LongMission|Tag.SlowEnemy),
    Enemy("Omnd-Omnd-Ohk",
        Pawn("PawnBalance_Native_Badass", transform=3),
        Pawn("PawnBalance_Nast_Native_Badass", transform=3),
    tags=Tag.HammerlocksHunt|Tag.EvolvedEnemy|Tag.VeryRareEnemy),
    Enemy("Dexiduous the Invincible",
        Pawn("PawnBalance_DrifterRaid"),
        Behavior("GD_DrifterRaid.Anims.Anim_Raid_Death:BehaviorProviderDefinition_29.Behavior_SpawnItems_38", inject=False),
    tags=Tag.HammerlocksHunt|Tag.RaidEnemy|Tag.SlowEnemy),

    Enemy("Mister Boney Pants Guy", Pawn("PawnBalance_BoneyPants"), tags=Tag.DragonKeep),
    Enemy("Treant",
        Pawn("PawnBalance_Treant"),
        Pawn("PawnBalance_Treant_StandStill"),
        Pawn("PawnBalance_Treant_StandStill_OL"),
        Pawn("PawnBalance_Treant_Overleveled"),
    tags=Tag.DragonKeep),
    Enemy("Warlord Grug", Pawn("PawnBalance_Orc_WarlordGrug", evolved=4), tags=Tag.DragonKeep),
    Enemy("Warlord Turge", Pawn("PawnBalance_Orc_WarlordTurge", evolved=4), tags=Tag.DragonKeep),
    Enemy("Duke of Ork",
        Pawn("PawnBalance_Orc_WarlordGrug", transform=4),
        Pawn("PawnBalance_Orc_WarlordTurge", transform=4),
    tags=Tag.DragonKeep|Tag.EvolvedEnemy),
    Enemy("Arguk the Butcher", Pawn("PawnBalance_Orc_Butcher"), mission="Critical Fail"),
    Enemy("-=nOObkiLLer=-", Pawn("PawnBalance_Knight_LostSouls_Invader"), mission="Lost Souls"),
    Enemy("xxDatVaultHuntrxx", Pawn("PawnBalance_Knight_MMORPG1"), mission="MMORPGFPS", rarities=(7,)),
    Enemy("420_E-Sports_Masta", Pawn("PawnBalance_Knight_MMORPG2"), mission="MMORPGFPS", rarities=(7,)),
    Enemy("[720NoScope]Headshotz", Pawn("PawnBalance_Knight_MMORPG3"), mission="MMORPGFPS", rarities=(7,)),
    Enemy("King Aliah", Pawn("PawnBalance_SkeletonKing_Aliah"), tags=Tag.DragonKeep|Tag.SlowEnemy),
    Enemy("King Crono", Pawn("PawnBalance_SkeletonKing_Crono"), tags=Tag.DragonKeep|Tag.SlowEnemy),
    Enemy("King Seth", Pawn("PawnBalance_SkeletonKing_Seth"), tags=Tag.DragonKeep|Tag.SlowEnemy),
    Enemy("King Nazar", Pawn("PawnBalance_SkeletonKing_Nazar"), tags=Tag.DragonKeep|Tag.SlowEnemy),
    Enemy("Unmotivated Golem", Pawn("PawnBalance_Golem_SwordInStone"), mission="The Sword in The Stoner"),
    Enemy("Spiderpants", Pawn("PawnBalance_Spiderpants"), tags=Tag.DragonKeep|Tag.VeryRareEnemy|Tag.SlowEnemy),
    Enemy("Maxibillion", Pawn("PawnBalance_GolemFlying_Maxibillion"), mission="My Kingdom for a Wand", rarities=(5,)),
    Enemy("Magical Spider", Pawn("PawnBalance_Spider_ClaptrapWand"), mission="My Kingdom for a Wand", rarities=(5,)),
    Enemy("Magical Orc", Pawn("PawnBalance_Orc_ClaptrapWand"), mission="My Kingdom for a Wand", rarities=(5,)),
    Enemy("Iron GOD", Pawn("PawnBalance_Golem_Badass", transform=5), tags=Tag.DragonKeep|Tag.SlowEnemy|Tag.EvolvedEnemy|Tag.RaidEnemy),
    Enemy("Gold Golem", Pawn("PawnBalance_GolemGold"), tags=Tag.DragonKeep|Tag.SlowEnemy, rarities=(33,33,33)),
    Enemy("The Darkness", Pawn("PawnBalance_Darkness"), tags=Tag.DragonKeep),
    Enemy("Sir Boil", Pawn("PawnBalance_SirBoil"), mission="Loot Ninja"),
    Enemy("Sir Mash", Pawn("PawnBalance_SirMash"), mission="Loot Ninja"),
    Enemy("Sir Stew", Pawn("PawnBalance_SirStew"), mission="Loot Ninja"),

    Enemy("Sorcerer", Pawn("PawnBalance_Sorcerer"), tags=Tag.DragonKeep),
    Enemy("Fire Mage", Pawn("PawnBalance_FireMage"), tags=Tag.DragonKeep),
    Enemy("Necromancer", Pawn("PawnBalance_Necromancer"), tags=Tag.DragonKeep),
    Enemy("Wizard", Pawn("PawnBalance_Wizard"), mission="Magic Slaughter: Round 3", tags=Tag.RareEnemy),
    Enemy("Badass Sorcerer", Pawn("PawnBalance_Sorcerer_Badass"), tags=Tag.DragonKeep),
    Enemy("Badass Fire Mage", Pawn("PawnBalance_FireMage_Badass"), tags=Tag.DragonKeep),
    Enemy("Badass Necromancer", Pawn("PawnBalance_Necro_Badass"), tags=Tag.DragonKeep),
    Enemy("Badass Wizard", Pawn("PawnBalance_Wizard_Badass"), mission="Magic Slaughter: Badass Round", tags=Tag.RareEnemy),
    Enemy("Canine", Pawn("PawnBalance_Knight_Winter_Canine"), mission="Winter is a Bloody Business"),
    Enemy("Molehill", Pawn("PawnBalance_Knight_Winter_Molehill"), mission="Winter is a Bloody Business"),
    Enemy("Handsome Dragon",
        # Pawn("PawnBalance_DragonBridgeBoss"),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_26"),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_17", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_18", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_19", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_20", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_21", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_27", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_28", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_29", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_31", inject=False),
    tags=Tag.DragonKeep, rarities=(33,33,33)),
    Enemy("Edgar", Pawn("PawnBalance_Wizard_DeadBrotherEdgar"), mission="My Dead Brother (Kill Edgar)"),
    Enemy("Simon", Pawn("PawnBalance_Wizard_DeadBrotherSimon"), mission="My Dead Brother (Kill Edgar)"),
    Enemy("Sorcerer's Daughter", Pawn("PawnBalance_AngelBoss"), tags=Tag.DragonKeep|Tag.SlowEnemy, rarities=(33,33,33)),
    Enemy("Handsome Sorcerer",
        Behavior("GD_ButtStallion_Proto.Character.AIDef_ButtStallion_Proto:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_46"),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_32"),
        Behavior("GD_ButtStallion_Proto.Character.AIDef_ButtStallion_Proto:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_43", inject=False),
        Behavior("GD_ButtStallion_Proto.Character.AIDef_ButtStallion_Proto:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_44", inject=False),
        Behavior("GD_ButtStallion_Proto.Character.AIDef_ButtStallion_Proto:AIBehaviorProviderDefinition_1.Behavior_SpawnItems_45", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_53", inject=False),
        Behavior("GD_DragonBridgeBoss.InteractiveObjects.IO_DragonBridgeBoss_LootExplosion:BehaviorProviderDefinition_0.Behavior_SpawnItems_30", inject=False),
    tags=Tag.DragonKeep|Tag.SlowEnemy, rarities=(33,33,33)),
    Enemy("The Ancient Dragons of Destruction",
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_706"),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_702", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_703", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_704", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_705", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_707", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_708", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_709", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_710", inject=False),
        Behavior("GD_Aster_RaidBossData.IOs.IO_LootSpewer:BehaviorProviderDefinition_0.Behavior_SpawnItems_711", inject=False),
    tags=Tag.DragonKeep|Tag.RaidEnemy),
    Enemy("Warlord Slog", Pawn("PawnBalance_Orc_WarlordSlog", evolved=4), mission="Magic Slaughter: Badass Round"),
    Enemy("King of Orks", Pawn("PawnBalance_Orc_WarlordSlog", transform=4), mission="Magic Slaughter: Badass Round", tags=Tag.EvolvedEnemy),

    Enemy("Sand Worm",
        Pawn("PawnBalance_SandWorm_Queen"),
        Pawn("PawnBalance_InfectedSandWorm"),
    tags=Tag.FightForSanctuary|Tag.MobFarm),
    Enemy("New Pandora Soldier",
        Pawn("PawnBalance_Flamer"),
        Pawn("PawnBalance_NP_Enforcer"),
        Pawn("PawnBalance_NP_BadassSniper"),
        Pawn("PawnBalance_NP_Commander"),
        Pawn("PawnBalance_NP_Enforcer"),
        Pawn("PawnBalance_NP_Infecto"),
        Pawn("PawnBalance_NP_Lt_Angvar"),
        Pawn("PawnBalance_NP_Lt_Tetra"),
        Pawn("PawnBalance_NP_Medic"),
    tags=Tag.FightForSanctuary|Tag.MobFarm),
    Enemy("Infected Badass Sprout", Pawn("PawnBalance_Infected_Badass_Midget"), tags=Tag.FightForSanctuary|Tag.MobFarm, rarities=(7,)),
    Enemy("Ghost", Pawn("PawnBalance_Ghost"), tags=Tag.FightForSanctuary),
    Enemy("Uranus", Pawn("PawnBalance_Uranus"), tags=Tag.FightForSanctuary|Tag.SlowEnemy),
    Enemy("Cassius", Pawn("PawnBalance_Anemone_Cassius"), tags=Tag.FightForSanctuary),
    Enemy("Loot Midget (Space Cowboy)", SpaceCowboyMidget("PawnBalance_LootMidget_Marauder"), mission="Space Cowboy"),
    Enemy("Dr. Zed's Experiment",
        Pawn("PawnBalance_Anemone_Slagsteins1"),
        Pawn("PawnBalance_Anemone_Slagsteins2"),
    mission="Hypocritical Oath"),
    Enemy("The Dark Web", Pawn("PawnBalance_Anemone_TheDarkWeb"), mission="Claptocurrency"),
    Enemy("Lt. Bolson", Pawn("PawnBalance_Lt_Bolson"), tags=Tag.FightForSanctuary|Tag.SlowEnemy),
    Enemy("Lt. Angvar", Pawn("PawnBalance_NP_Lt_Angvar"), tags=Tag.FightForSanctuary|Tag.SlowEnemy),
    Enemy("Lt. Tetra", Pawn("PawnBalance_NP_Lt_Tetra"), tags=Tag.FightForSanctuary|Tag.SlowEnemy),
    Enemy("Lt. Hoffman", Pawn("PawnBalance_NP_Lt_Hoffman"), tags=Tag.FightForSanctuary|Tag.SlowEnemy),
    Enemy("Bandit Leader (Nomad)", Pawn("PawnBalance_NomadBadass_Leader"), mission="The Vaughnguard"),
    Enemy("Bandit Leader (Marauder)", Pawn("PawnBalance_MarauderBadass_Leader"), mission="The Vaughnguard"),
    Enemy("Haderax The Invincible",
        Behavior("GD_Anemone_SandWormBoss_1.Character.BodyDeath_Anemone_SandWormBoss_1:BehaviorProviderDefinition_2.Behavior_SpawnItems_5", inject=False),
        HaderaxChest("ObjectGrade_DalhEpicCrate_Digi"),
        HaderaxChest("ObjectGrade_DalhEpicCrate_Digi_PeakOpener"),
        HaderaxChest("ObjectGrade_DalhEpicCrate_Digi_Shield"),
        HaderaxChest("ObjectGrade_DalhEpicCrate_Digi_Articfact"),
    tags=Tag.FightForSanctuary|Tag.RaidEnemy, rarities=(75,75,75,75)),

    Enemy("The Rat in the Hat", Pawn("PawnBalance_RatChef"), mission="The Hunger Pangs"),
    Enemy("Chef Gouda Remsay", Pawn("PawnBalance_ButcherBoss"), mission="The Hunger Pangs"),
    Enemy("Chef Brulee", Pawn("PawnBalance_ButcherBoss2"), mission="The Hunger Pangs"),
    Enemy("Chef Bork Bork", Pawn("PawnBalance_ButcherBoss3"), mission="The Hunger Pangs"),
    Enemy("Glasspool, Tribute of Wurmwater", Pawn("PawnBalance_SandMale"), mission="The Hunger Pangs"),
    Enemy("William, Tribute of Wurmwater", Pawn("PawnBalance_SandFemale"), mission="The Hunger Pangs"),
    Enemy("Axel, Tribute of Opportunity", Pawn("PawnBalance_EngineerMale"), mission="The Hunger Pangs"),
    Enemy("Rose, Tribute of Opportunity", Pawn("PawnBalance_EngineerFemale"), mission="The Hunger Pangs"),
    Enemy("Fiona, Tribute of Sanctuary", Pawn("PawnBalance_RaiderFemale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Max, Tribute of Sanctuary", Pawn("PawnBalance_RaiderMale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Strip, Tribute of Southern Shelf", Pawn("PawnBalance_FleshripperFemale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Flay, Tribute of Southern Shelf", Pawn("PawnBalance_FleshripperMale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Fuse, Tribute of Frostburn", Pawn("PawnBalance_IncineratorMale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Cynder, Tribute of Frostburn", Pawn("PawnBalance_IncineratorFemale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Annie, Tribute of Lynchwood", Pawn("PawnBalance_Lynchwood_Female"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Garret, Tribute of Lynchwood", Pawn("PawnBalance_Lynchwood_Male"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Moretus, Tribute of Sawtooth Cauldron", Pawn("PawnBalance_CraterMale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Bailly, Tribute of Sawtooth Cauldron", Pawn("PawnBalance_CraterFemale"), tags=Tag.WattleGobbler|Tag.RareEnemy),
    Enemy("Ravenous Wattle Gobbler",
        Pawn("PawnBalance_BigBird"),
        Pawn("PawnBalance_BigBird_HARD"),
    tags=Tag.WattleGobbler|Tag.SlowEnemy),

    Enemy("The Abominable Mister Tinder Snowflake",
        Pawn("PawnBalance_SnowMan"),
        Pawn("PawnBalance_SnowMan_HARD"),
        Behavior("GD_Snowman.Death.BodyDeath_SnowMan:BehaviorProviderDefinition_6.Behavior_SpawnItems_9", inject=False),
    tags=Tag.MercenaryDay|Tag.SlowEnemy),

    Enemy("Enchanted Skeleton", Pawn("PawnBalance_HallowSkeletonEnchanted"), mission="The Bloody Harvest"),
    Enemy("Sully the Blacksmith", Pawn("PawnBalance_Spycho"), mission="The Bloody Harvest"),

    Enemy("Pumpkin Kingpin/Jacques O'Lantern",
        Behavior("GD_PumpkinheadFlying.Character.DeathDef_Pumpkinheadflying:BehaviorProviderDefinition_0.Behavior_SpawnItems_209"),
        Behavior("GD_Flax_Lootables.IOs.IO_Pumpkin_BossLoot:BehaviorProviderDefinition_1.Behavior_SpawnItems_210", inject=False),
    tags=Tag.BloodyHarvest|Tag.SlowEnemy, rarities=(33,33,33)),
    Enemy("Clark the Combusted Cryptkeeper", Pawn("PawnBalance_UndeadFirePsycho_Giant"), tags=Tag.BloodyHarvest|Tag.SlowEnemy, rarities=(100,100,50)),

    Enemy("Son of Crawmerax the Invincible", Pawn("PawnBalance_Crawmerax_Son"), tags=Tag.SonOfCrawmerax|Tag.SlowEnemy, rarities=(33,33,33)),
    Enemy("The Invincible Son of Crawmerax the Invincible",
        # TODO test disappearing loot from pawn; maybe switch to behavior
        Pawn("PawnBalance_Crawmerax_Son_Raid"),
        Behavior("GD_Nasturtium_Lootables.IOs.IO_BossLootSpout:BehaviorProviderDefinition_0.Behavior_SpawnItems_502", inject=False),
        Behavior("GD_Nasturtium_Lootables.IOs.IO_BossLootSpout:BehaviorProviderDefinition_0.Behavior_SpawnItems_6", inject=False),
        Behavior("GD_Nasturtium_Lootables.IOs.IO_BossLootSpout:BehaviorProviderDefinition_0.Behavior_SpawnItems_7", inject=False),
        Behavior("GD_Nasturtium_Lootables.IOs.IO_BossLootSpout:BehaviorProviderDefinition_0.Behavior_SpawnItems_8", inject=False),
    tags=Tag.SonOfCrawmerax|Tag.RaidEnemy|Tag.SlowEnemy),
    Enemy("Sparky, Son of Flynt", Pawn("PawnBalance_FlyntSon"), tags=Tag.SonOfCrawmerax|Tag.SlowEnemy),

    Enemy("BLNG Loader", Pawn("PawnBalance_BlingLoader"), mission="A Match Made on Pandora"),
    Enemy("Colin Zaford",
        Pawn("PawnBalance_GoliathGroom", evolved=5),
        Pawn("PawnBalance_GoliathGroomRaid", evolved=5),
        Behavior("GD_GoliathGroom.Death.BodyDeath_GoliathGroom:BehaviorProviderDefinition_6.Behavior_SpawnItems_8", inject=False),
    tags=Tag.WeddingDayMassacre|Tag.SlowEnemy),
    Enemy("Bridget Hodunk",
        Pawn("PawnBalance_GoliathBride", evolved=5),
        Pawn("PawnBalance_GoliathBrideRaid", evolved=5),
        Behavior("GD_GoliathBride.Death.BodyDeath_GoliathBride:BehaviorProviderDefinition_6.Behavior_SpawnItems_12", inject=False),
    tags=Tag.WeddingDayMassacre|Tag.SlowEnemy),
    Enemy("Sigmand", Pawn("PawnBalance_Nast_ThresherWhite"), tags=Tag.WeddingDayMassacre),
    Enemy("Ikaroa", Pawn("PawnBalance_Nast_ThresherGreen"), tags=Tag.WeddingDayMassacre),
    Enemy("Moby", Pawn("PawnBalance_Nast_ThresherBlue"), tags=Tag.WeddingDayMassacre|Tag.SlowEnemy),
    Enemy("Fire Crak'n", Pawn("PawnBalance_Nast_ThresherPurple"), tags=Tag.WeddingDayMassacre|Tag.SlowEnemy),
    Enemy("Rue, The Love Thresher", Pawn("PawnBalance_Nast_ThresherOrange"), tags=Tag.WeddingDayMassacre|Tag.SlowEnemy),
    Enemy("Ed", Pawn("PawnBalance_BadassJunkLoader"), mission="Learning to Love"),
    Enemy("Stella", Pawn("PawnBalance_LoaderGirl"), mission="Learning to Love"),
    Enemy("Innuendobot 5000", Pawn("PawnBalance_Innuendobot_NPC"), mission="Learning to Love"),

    DigiEnemy("Digistruct Scorch", Pawn("PawnBalance_SpiderantScorch_Digi"), fallback="Scorch", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(50, 50)),
    DigiEnemy("Digistruct Dukino's Mom", Pawn("PawnBalance_Skagzilla_Digi"), fallback="Dukino's Mom", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 33, 33)),
    DigiEnemy("Digistruct Black Queen", Pawn("PawnBalance_SpiderantBlackQueen_Digi"), fallback="The Black Queen", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 33)),
    DigiEnemy("Bone Head v3.0", Pawn("PawnBalance_BoneHead_V3"), fallback="Bone Head 2.0", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(50, 50)),
    DigiEnemy("Digistruct Doc Mercy", Pawn("PawnBalance_MrMercy_Digi"), fallback="Doc Mercy", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 50)),
    DigiEnemy("Digistruct Assassin Wot", Pawn("PawnBalance_Assassin1_Digi"), fallback="Assassin Wot", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 100, 50)),
    DigiEnemy("Digistruct Assassin Oney", Pawn("PawnBalance_Assassin2_Digi"), fallback="Assassin Oney", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 100, 50)),
    DigiEnemy("Digistruct Assassin Reeth", Pawn("PawnBalance_Assassin3_Digi"), fallback="Assassin Reeth", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 100, 50)),
    DigiEnemy("Digistruct Assassin Rouf", Pawn("PawnBalance_Assassin4_Digi"), fallback="Assassin Rouf", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 100, 50)),
    DigiEnemy("Saturn v2.0", Pawn("PawnBalance_LoaderUltimateBadass_Digi"), fallback="Saturn", tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 100, 50, 50)),
    Enemy("010011110100110101000111-010101110101010001001000",
        Pawn("PawnBalance_SpiderTank_Boss"),
        Behavior("GD_SpiderTank_Boss.Death.DeathDef_SpiderTank_Boss:BehaviorProviderDefinition_0.Behavior_SpawnItems_42", inject=False),
        Behavior("GD_SpiderTank_Boss.Death.DeathDef_SpiderTank_Boss:BehaviorProviderDefinition_0.Behavior_SpawnItems_43", inject=False),
        Behavior("GD_SpiderTank_Boss.Death.DeathDef_SpiderTank_Boss:BehaviorProviderDefinition_0.Behavior_SpawnItems_44", inject=False),
        Behavior("GD_SpiderTank_Boss.Death.DeathDef_SpiderTank_Boss:BehaviorProviderDefinition_0.Behavior_SpawnItems_45", inject=False),
        Behavior("GD_SpiderTank_Boss.Death.DeathDef_SpiderTank_Boss:BehaviorProviderDefinition_0.Behavior_SpawnItems_46", inject=False),
        Behavior("GD_SpiderTank_Boss.Death.DeathDef_SpiderTank_Boss:BehaviorProviderDefinition_0.Behavior_SpawnItems_47", inject=False),
    tags=Tag.DigistructPeak|Tag.DigistructEnemy, rarities=(100, 100, 100, 50, 50, 50, 33, 33, 33)),
)