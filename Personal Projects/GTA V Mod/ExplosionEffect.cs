using GTA;
using GTA.Math;

public class ExplosionEffect : IEffect
{
    public string Name => "Explosion nearby!";

    public void Execute()
    {
        var player = Game.Player.Character;
        World.AddExplosion(player.Position + new Vector3(10f, 10f, 0f), ExplosionType.Car, 5f, 1f);
        GTA.UI.Notification.Show($"~r~Randomizer Effect:~w~ {Name}");
    }
}