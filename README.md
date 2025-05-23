# Note About This Fork

This fork of Loot Randomizer integrates the online tracker functionality from [bl2_loot_tracker](https://github.com/soopsman/bl2_loot_tracker) directly into the mod.

The settings can be found in the Configure Seed Tracker section.

If you previously used bl2_loot_tracker, you can migrate your existing GitHub settings from the appsettings.json and gists.json of the original tracker into sdk_mods\settings\LootRandomizer.json.

| LootRandomizer.json | Original Location |
| ------------------- | ----------------- |
| Github Token | appsetting.json - Token |
| Github Gist Id | gists.json - Id |
| Github Gist Url |  gists.json - Url |
| Last Seed Updated | gists.json - (seed value) |

You are required to launch the game once with this fork of the mod enabled to create the entries in LootRandomizer.json.

# Borderlands Loot Randomizer

[Discord](https://discord.gg/C37HvmvBbS)&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;[Donate](https://streamlabs.com/mopioid/tip)

![Face McTwisty](https://i.imgur.com/OIZ9Ab4.jpeg)

Loot Randomizer is a mod for Borderlands 2 and The Pre-Sequel that provides repeated new playthrough experiences, by means of shuffling every item in the game into new drop locations.

When playing Loot Randomizer, you create a seed, and your game's loot sources are assigned all new drops based on that seed. Your Knuckle Dragger may drop the Norfleet, while your Hyperius drops The Cradle.

In addition to enemies, missions are also assigned new quest rewards, and made to be infinitely repeatable such that they can be farmed without resetting your playthrough. Your "Shoot This Guy In The Face" mission may reward a purple Jakobs sniper each turn-in, while your "Beard Makes The Man" mission gives Lucrative Opportunity relics.

Each loot source had been hand-tuned to provide fair loot generosity. Longer missions give multiple instances of their quest reward, for example, and raid bosses drop multiple of their assigned drop guaranteed. If you don't get a drop from an enemy on the first try, they will drop a "hint" item instead, giving you the option to decide whether to keep farming them.

Seeds can be configured with different options regarding what types of content to include, such as the ability to disable rare enemies or enable raid bosses. They can also be shared with friends (for fun competitive scenarios), and can accomodate any DLCs being owned or unowned.

Loot Randomizer works in co-op, with the best experience if all players run the mod (however this is not strictly necessary). The host player's seed will be the one which is in effect in co-op. Loot Randomizer is also compatible with most other mods, including major overhauls (e.g. UCP, BL2fix, Reborn). However, others which increase the number of items or enemies in the game will not fully integrate with it (e.g. Exodus). 

## Installation

See: https://github.com/mopioid/Borderlands-Loot-Randomizer/wiki/Installation

## Getting Started

To get started playing Loot Randomizer, first enable the mod from the Mods menu in the main menu. 

Next, navigate to Options > Mods, and you will see a section for Loot Randomizer. Begin by clicking "New Seed," configuring your preferred options, and clicking "Generate" to create and apply it. You can now start exploring in game!

To learn more about the seed you just created, navigate to Options > Mods > Loot Randomizer, and select the "View Seed Tracker" button. This will open a text file listing every possible drop source that you can explore, and will also be updated with information on their drops as you learn it during gameplay.

To learn more about the items, locations, and seed generation in Loot Randomizer, see:

https://github.com/mopioid/Borderlands-Loot-Randomizer/wiki/Items

https://github.com/mopioid/Borderlands-Loot-Randomizer/wiki/Locations

## Support

Loot Randomizer is the product of hundreds of hours of loving labor. Tips are far from necessary, but if you appreciate the experience enough and would like to leave one, feel free to here! https://streamlabs.com/mopioid/tip
