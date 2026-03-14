// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "ResetManagerSDT.h"
#include "EngineUtils.h"
#include "Math/UnrealMathUtility.h"
#include "CoreMinimal.h"
#include "../ActionManagers/ActionManagerSDT.h"
#include "../LevelManager/ActorTarget.h"
#include "GameFramework/Actor.h"
#include "LevelResetManagerSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API ALevelResetManagerSDT : public AActor, public IResetManagerSDT
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	ALevelResetManagerSDT();
	void Reset();

	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | PawnAgent")
		APawn* PawnAgent; //will be casted

	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | ActorTarget")
		AActor* ActorTarget; //will be casted 

	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | ActorToSpawn")
		TArray<AActor*> ActorsToSpawn; // Could be empty!


	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | FloorName")
		TArray<FString> FloorNames; //define level
	
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
		UStaticMeshComponent* Mesh;		//uncollidable. Define a mesh is necessary for positioning inside a "level"

	FHitResult* ActorHit; //used for random spawn
	UPROPERTY()
		TMap<FString, float> ZFloors;
	UPROPERTY()
		TMap<FString, float> XMaxFloors;
	UPROPERTY()
		TMap<FString, float> XMinFloors;
	UPROPERTY()
		TMap<FString, float> YMaxFloors;
	UPROPERTY()
		TMap<FString, float> YMinFloors;



protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;
	bool CheckInitSettings();
	FString ParseClassName(FString String);
	
	IActionManagerSDT* PawnAgentCasted;
	UPROPERTY()
		AActorTarget* ActorTargetCasted;



public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;
	virtual const FString GetResetManagerName() const override;
	virtual const bool PerformReset(TArray<FString>& FieldArray) override;
	virtual const bool ChangeResetSettings(const TArray<FString>& Settings) override;

};
