using GTA;
using GTA.Math;
using System;
using System.Threading.Tasks;

public class DrunkCinematicEffect : IEffect
{
    public string Name => "Wild Chaos & Motion Boost!";

    public void Execute()
    {
        var player = Game.Player.Character;
        GTA.UI.Notification.Show($"~r~Randomizer Effect:~w~ {Name}");

        // Apply a fun chaotic effect safely
        if (player.IsInVehicle())
        {
            // Give the vehicle a sudden burst of speed
            if (player.CurrentVehicle != null)
            {
                player.CurrentVehicle.Speed *= 1.8f;
            }
        }
        else
        {
            // Launch the player slightly into the air with a sudden force
            player.ApplyForce(new Vector3(0f, 0f, 7.5f));
        }

        // Run a background timer for 2 minutes (120,000 ms)
        Task.Delay(120000).ContinueWith(_ =>
        {
            if (player.Exists())
            {
                GTA.UI.Notification.Show("~g~Chaos effect wore off!");
            }
        });
    }
}