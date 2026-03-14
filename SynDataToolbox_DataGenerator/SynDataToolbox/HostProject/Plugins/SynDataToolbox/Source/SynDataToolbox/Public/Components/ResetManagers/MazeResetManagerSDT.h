// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "ResetManagerSDT.h"
#include "EngineUtils.h"
#include "Math/UnrealMathUtility.h"
#include <cmath>
#include "CoreMinimal.h"
#include "../ActionManagers/ActionManagerSDT.h"
#include "../LevelManager/ActorTarget.h"
#include "GameFramework/Actor.h"
#include "MazeResetManagerSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API AMazeResetManagerSDT : public AActor, public IResetManagerSDT
{
	GENERATED_BODY()

public:
	// Sets default values for this actor's properties
	AMazeResetManagerSDT();
	void Reset();

	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | PawnAgent")
		APawn* PawnAgent; //will be casted

	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | ActorTarget")
		AActor* ActorTarget; //will be casted 

	//Decide whether in the maze there are some false positives
	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | ActorToSpawn")
		TArray<AActor*> ActorsToSpawn; // Could be empty!

	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | MazeManagerName")
		AActor* MazeManager; //
	UPROPERTY(EditAnywhere, Category = "ResetManagerSettings | MazeSettings")
		bool bRegenerateMaze = true;


	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
		UStaticMeshComponent* Mesh;		//uncollidable. Define a mesh is necessary for positioning inside a "level"

	FHitResult* ActorHit; //used for random spawn

	UPROPERTY()
		FVector MazeOriginLocation;
	UPROPERTY()
		float FloorMeshWidth = 100;
	UPROPERTY()
		float FloorMeshHeight = 100;
	UPROPERTY()
		int MazeWidth;
	UPROPERTY()
		int MazeHeight;
	//UPROPERTY()
	//	float ZFloor;
	//UPROPERTY()
	//	float XMaxFloor;
	//UPROPERTY()
	//	float XMinFloor;
	//UPROPERTY()
	//	float YMaxFloor;
	//UPROPERTY()
	//	float YMinFloors;

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;
	bool CheckInitSettings();
	FString ParseClassName(FString String);

	IActionManagerSDT* PawnAgentCasted;
	AActorTarget* ActorTargetCasted;



public:
	// Called every frame
	virtual void Tick(float DeltaTime) override;
	virtual const FString GetResetManagerName() const override;
	virtual const bool PerformReset(TArray<FString>& FieldArray) override;
	virtual const bool ChangeResetSettings(const TArray<FString>& Settings) override;

};
