#pragma once

#include "CoreMinimal.h"
#include "../PhysicsControlManagers/PhysicsManagerSDT.h"
#include "AckermannPhysicsManagerSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API UAckermannPhysicsManagerSDT : public UObject, public IPhysicsManagerSDT
{

    GENERATED_BODY()

public:
    /** Add interface function declarations here */
    UAckermannPhysicsManagerSDT();

    virtual const FString GetPhysicsManagerName() const override;
    virtual void GetActorReference(AActor* Agent, FHitResult* ActorHit) override; //pointer for grab status info like position and rotation
    virtual bool Reset() override; //restore all current state variables
    virtual void SetPhysicsSettings(TArray<float> Settings) override; //mass, width, height, momentum limits, force limits
    virtual void SetNewPosition(TArray<float> Velocities, float DeltaTime, float IsRotAngle) override;

protected:
    FHitResult* HitHandler;

    UPROPERTY()
        AActor* AgentToManage;
    
    FVector OldPosition;
    FVector CurrentPosition;

    FRotator OldRotation;
    FRotator CurrentRotation;

    float RotationAngle;  // rotation angle

    UPROPERTY()
        TArray<float> CurrentVel; //linear; angular
    UPROPERTY()
        float AgentMass = 0.0f;
    UPROPERTY()
        float AgentLength = 0.0f;
    UPROPERTY()
        float AgentWidth = 0.0f;
    UPROPERTY()
        float MAX_FORCE = 0.0f;
    UPROPERTY()
        float MIN_FORCE= 0.0f;
    UPROPERTY()
        float MAX_MOMENTUM = 0.0f;
    UPROPERTY()
        float MIN_MOMENTUM = 0.0f;
    UPROPERTY()
        float FrictionParameter = 0.0f;
    UPROPERTY()
        float AngularFrictionParameter = 0.0f;
    UPROPERTY()
        float isAngleRot = true;
    UPROPERTY()
        float Current_Angular_Velocity = 0.0f;
    UPROPERTY()
        float Current_Angular_Acceleration = 0.0f;
};