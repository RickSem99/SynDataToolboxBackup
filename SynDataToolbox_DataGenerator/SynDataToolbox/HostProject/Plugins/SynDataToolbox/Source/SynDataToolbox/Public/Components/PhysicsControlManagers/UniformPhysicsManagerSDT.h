#pragma once

#include "CoreMinimal.h"
#include "../PhysicsControlManagers/PhysicsManagerSDT.h"
#include "UniformPhysicsManagerSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API UUniformPhysicsManagerSDT : public UObject, public IPhysicsManagerSDT
{

    GENERATED_BODY()

public:
    /** Add interface function declarations here */
    UUniformPhysicsManagerSDT();

    virtual const FString GetPhysicsManagerName() const override;
    virtual TArray<float> GetCurrentOutputs() override; //outputs of model
    virtual void GetActorReference(AActor* Agent, FHitResult* ActorHit) override; //pointer for grab status info like position and rotation
    virtual bool Reset() override; //restore all current state variables
    virtual void SetPhysicsSettings(TArray<float> Settings) override; //mass, width, height, momentum limits, force limits
    virtual TArray<float> Compute(TArray<float> RegulationVector) override; //RegulationVector contains values produced by PID

protected:
    FHitResult* HitHandler;

    UPROPERTY()
        AActor* AgentToManage;

    FVector OldPosition;
    FVector CurrentPosition;

    FRotator OldRotation;
    FRotator CurrentRotation;

    UPROPERTY()
        TArray<float> CurrentVel; //linear; angular
    //UPROPERTY()
    //    TArray<float> RegulationVector; //linear acc; angular acc. Given from PID
    UPROPERTY()
        float AgentMass = 0.0f;
    UPROPERTY()
        float AgentLength = 0.0f;
    UPROPERTY()
        float AgentWidth = 0.0f;
    UPROPERTY()
        float MAX_FORCE = 0.0f;
    UPROPERTY()
        float MIN_FORCE = 0.0f;
    UPROPERTY()
        float MAX_MOMENTUM = 0.0f;
    UPROPERTY()
        float MIN_MOMENTUM = 0.0f;
    UPROPERTY()
        float FrictionParameter = 0.0f;
    UPROPERTY()
        float AngularFrictionParameter = 0.0f;

    UPROPERTY()
        float Current_Linear_Velocity = 0.0f;
    UPROPERTY()
        float Current_Linear_Acceleration = 0.0f;
    UPROPERTY()
        float Current_Angular_Velocity = 0.0f;
    UPROPERTY()
        float Current_Angular_Acceleration = 0.0f;
};