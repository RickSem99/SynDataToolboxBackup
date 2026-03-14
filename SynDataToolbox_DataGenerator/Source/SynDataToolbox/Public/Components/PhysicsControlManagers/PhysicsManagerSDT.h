#pragma once
#include "PhysicsManagerSDT.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UPhysicsManagerSDT : public UInterface
{
    GENERATED_BODY()
};

class SYNDATATOOLBOX_API IPhysicsManagerSDT
{
    GENERATED_BODY()

public:
    /** Add interface function declarations here */
    virtual const FString GetPhysicsManagerName() const;
    virtual TArray<float> GetCurrentOutputs(); //outputs of model
    virtual void GetActorReference(AActor* Agent, FHitResult* ActorHit); //pointer for grab status info like position and rotation
    virtual bool Reset(); //restore all current state variables
    virtual void SetPhysicsSettings(TArray<float> Settings);
    virtual TArray<float> Compute(TArray<float> RegularizationValues); //return Current signal values (for our purpose, current velocities)
    virtual void SetNewPosition(TArray<float> Velocities, float DeltaTime, float IsRotAngle);
};