using GTA;
using GTA.Native;

public class LowGravityEffect : IEffect
{
    public string Name => "Low Gravity Activated!";

    public void Execute()
    {
        Function.Call(Hash.SET_GRAVITY_LEVEL, 2); // 2 sets low gravity mode
        GTA.UI.Notification.Show($"~r~Randomizer Effect:~w~ {Name}");
    }
}