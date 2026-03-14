#include "Components/PhysicsControlManagers/PhysicsManagerSDT.h"

const FString IPhysicsManagerSDT::GetPhysicsManagerName() const
{
    return FString("NO PHYSICS IMPLEMENTATION");
}

TArray<float> IPhysicsManagerSDT::GetCurrentOutputs()
{
    return TArray<float>();
}

void IPhysicsManagerSDT::GetActorReference(AActor* Agent, FHitResult* ActorHit)
{
}

bool IPhysicsManagerSDT::Reset()
{
    return false;
}

void IPhysicsManagerSDT::SetPhysicsSettings(TArray<float> Settings)
{
}

TArray<float> IPhysicsManagerSDT::Compute(TArray<float> Action)
{
    return TArray<float>();
}

void IPhysicsManagerSDT::SetNewPosition(TArray<float> Velocities, float DeltaTime, float IsRotAngle)
{
}
