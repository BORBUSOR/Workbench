using System;
using System.IO;
using GTA;

public class DiscordCommandListener : Script
{
    // Match your Python absolute path precisely
    private readonly string commandFilePath = @"D:\Grand Theft Auto V Legacy\scripts\gta_command.txt";

    public DiscordCommandListener()
    {
        Interval = 500; // Check twice a second for snappy response
        Tick += OnTick;
    }

    private void OnTick(object sender, EventArgs e)
    {
        try
        {
            if (File.Exists(commandFilePath))
            {
                string command = "";

                // Use FileShare.ReadWrite so Python and C# don't fight over file locks
                using (var fs = new FileStream(commandFilePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (var sr = new StreamReader(fs))
                {
                    command = sr.ReadToEnd().Trim().ToLower();
                }

                // Clear the file immediately after reading so it doesn't loop
                if (!string.IsNullOrEmpty(command))
                {
                    File.WriteAllText(commandFilePath, string.Empty);
                    ExecuteCommand(command);
                }
            }
        }
        catch (Exception ex)
        {
            // This will show up on your screen if something goes wrong, instead of failing silently
            GTA.UI.Notification.Show("~r~GTA Mod Error:~w~ " + ex.Message);
        }
    }

    private void ExecuteCommand(string cmd)
    {
        if (cmd == "modkill" || cmd == "kill")
        {
            ModGlobals.IsActive = false;
            GTA.UI.Notification.Show("~r~GTA V Mods Killed!~w~ Bot is still running.");
            return;
        }

        if (cmd == "enable" || cmd == "restart")
        {
            ModGlobals.IsActive = true;
            GTA.UI.Notification.Show("~g~GTA V Mods Re-enabled!");
            return;
        }

        // Ignore all commands if mods are killed
        if (!ModGlobals.IsActive) return;

        switch (cmd)
        {
            case "random": GetRandomEffect()?.Execute(); break;
            case "gravity": new LowGravityEffect().Execute(); break;
            case "cows": new SpawnCowsEffect().Execute(); break;
            case "rpg": new RocketLauncherChaosEffect().Execute(); break;
            case "speed": new SpeedBoostEffect().Execute(); break;
            case "car": new SpawnRandomCarEffect().Execute(); break;
            case "explosion": new ExplosionEffect().Execute(); break;
            case "drunk": new DrunkCinematicEffect().Execute(); break;
        }
    }

    private IEffect GetRandomEffect()
    {
        var effects = new IEffect[]
        {
            new SpawnRandomCarEffect(),
            new LowGravityEffect(),
            new ExplosionEffect(),
            new SpeedBoostEffect(),
            new SpawnCowsEffect(),
            new RocketLauncherChaosEffect(),
            new DrunkCinematicEffect()
        };
        Random rand = new Random();
        return effects[rand.Next(effects.Length)];
    }
}