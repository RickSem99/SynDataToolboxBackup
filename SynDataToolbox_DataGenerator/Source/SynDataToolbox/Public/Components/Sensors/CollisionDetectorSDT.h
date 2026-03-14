// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "SensorSDT.h"
#include "GameFramework/Actor.h"
#include <Components/ActionManagers/ActionManagerSDT.h>
#include "CollisionDetectorSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API ACollisionDetectorSDT : public AActor, public ISensorSDT
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	ACollisionDetectorSDT();

	UPROPERTY(EditAnywhere, Category = "SensorProperties | SensorSettings")
		APawn* PawnAgent;

	UPROPERTY(EditAnywhere, Category = "SensorProperties | SensorSettings")
		AActor* ActorTarget;

	UPROPERTY(EditAnywhere, Category = "SensorProperties | Observation")
		float TimeSampling = 0.0f; //if null, by default every tick Actor get relative observation

	UPROPERTY(EditAnywhere, Category = "SensorProperties | Observation")
		bool enableIndependentTick = false;

	UPROPERTY(VisibleAnywhere, Category = "SensorProperties | Observation")
		FString LastObservationTimestamp; //
	
	UPROPERTY(VisibleAnywhere, Category = "SensorProperties | Observation")
		uint8 HasCollided; //

	UPROPERTY(EditAnywhere, Category = "SensorProperties | Observation")
		bool bEnvStep = false;

	bool bIsBusy = false; // reader-Writer sync



	uint8* LastObservation;
	FHitResult* ActorHit;

	UPROPERTY()
		UStaticMeshComponent* Mesh;

	virtual const FString GetSensorName() override;
	virtual const FString GetSensorSetup() override;
	virtual const uint32 GetObservationSize() override;
	virtual const bool InitSensor() override;
	virtual const bool ChangeSensorSettings(const TArray<FString>& settings) override;
	virtual const bool GetLastObs(uint8* Buffer) override;
	virtual const bool TakeObs() override; //the previous GetSensorObs
	
	const void SetTickMode(bool Value); //Actor hero can sospend tick of this actor?

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;
	UFUNCTION()
	void TakePeriodicObs();
	IActionManagerSDT* CastedPawnAgent;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
