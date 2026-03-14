// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "ActionManagerSDT.h"
#include <cmath>
#include <GameFramework/SpringArmComponent.h>
#include <Camera/CameraComponent.h>
#include "../PhysicsControlManagers/PhysicsManagerSDT.h"
#include "../PhysicsControlManagers/AckermannPhysicsManagerSDT.h"
//#include "../PhysicsControlManagers/PIDManagerSDT.h"
//#include "../PhysicsControlManagers/ProportionalPIDManagerSDT.h"
#include "AckermannActionManagerSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API AAckermannActionManagerSDT : public APawn, public IActionManagerSDT
{
	GENERATED_BODY()

public:
	// Sets default values for this pawn's properties
	AAckermannActionManagerSDT();

	// Called to bind functionality to input. Useless in this case
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	virtual const FString GetActionManagerName() const override;
	virtual const FString GetActionManagerSetup() const override; 	//in this method are stored commands and other setup info
	virtual const bool InitSettings(const TArray<FString>& Settings) override; //useless with new api version
	virtual const int8_t PerformAction(TArray<FString>& Action) override;
	virtual const int ActionToID(const FString& Action) const override;
	virtual FHitResult* GetHitHandler() override;
	virtual void Possess() override;
	virtual void UnPossess() override;

	void ResetPhysics();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;
	
	//compute "physics"
	const int8_t PositionComputation(float DeltaTime);

	//command-id
	static const int UNKNOWN = -1;
	static const int UPDATESETPOINTS = 1; //when someone pass desidered velocity (linear and angular)
	
	//action executor
	int8_t ChangeSetPoints(TArray<FString>& ActionSettings);
	FHitResult* ActorHit;
	float dt = 0.0;
	
	UPROPERTY()
		TScriptInterface<IPhysicsManagerSDT> PhysicsSolver;

	//UPROPERTY()
	//	TScriptInterface<IPIDManagerSDT> PIDRegulator;

	UPROPERTY()
	TArray<float> CurrentValues;

	UPROPERTY()
		TArray<float> CurrentVel; //linear; angular

	UPROPERTY()
		float TargetLinearVelocity;

	UPROPERTY()
		float TargetAngularVelocity;

	UPROPERTY()
		USpringArmComponent* CameraSpringArm;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
		UStaticMeshComponent* Mesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
		UCameraComponent* CameraComponent;

	//*property to display into element-details panel*/
	//UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
	//	FVector CurrentPosition; //the only one visible
	//
	//FVector OldPosition;

	//UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
	//	FRotator CurrentRotation;
	//
	//FRotator OldRotation;

	UPROPERTY(VisibleAnywhere, Category = "ActionManagerProperties | Simulation")
		FString CurrentPhysicsManager = "UNSET";

	//UPROPERTY(VisibleAnywhere, Category = "ActionManagerProperties | Simulation")
	//	FString CurrentPIDManager = "UNSET";

	UPROPERTY(VisibleAnywhere, Category = "ActionManagerProperties | Simulation")
		float CurrentLinearVelocity = 0.0f; //m/s 

	UPROPERTY(VisibleAnywhere, Category = "ActionManagerProperties | Simulation")
		float CurrentLinearAcceleration = 0.0f; //m/s^2 

	UPROPERTY(VisibleAnywhere, Category = "ActionManagerProperties | Simulation")
		float CurrentAngularVelocity = 0.0f; //rad/s

	UPROPERTY(VisibleAnywhere, Category = "ActionManagerProperties | Simulation")
		float CurrentAngularAcceleration = 0.0f; //rad/s^2

	/* control targets*/
	
	//in kg
	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float AgentMass = 0; 

	//in cm
	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float AgentLength = 0; 
	
	//in cm
	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float AgentWidth = 0; 

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float FrictionParameter = 0.99; //
	
	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float AngularFrictionParameter = 0.99; //
	//m/s. Sign indicates direction

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float MAX_FORCE = 100.0f;

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float MAX_MOMENTUM = 100.0f;

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float MIN_FORCE = -100.0f;

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float MIN_MOMENTUM = -100.0f;

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Physics")
		float isRotAngle = 1.0f;

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Simulation")
		float LinearMultiplexFactor = 1.0f;

	UPROPERTY(EditAnywhere, Category = "ActionManagerProperties | Simulation")
		float AngularMultiplexFactor = 1.0f;

	UPROPERTY()
		bool bCollision = false;

public:	
	virtual void Tick(float DeltaTime) override;


};
