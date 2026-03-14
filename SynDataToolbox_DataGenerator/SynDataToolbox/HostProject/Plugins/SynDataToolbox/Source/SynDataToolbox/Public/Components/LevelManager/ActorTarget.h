// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ActorTarget.generated.h"

/*Dummy Actor with transparent mesh. Used only in RL learning. (Terminal State episodic task)*/

UCLASS()
class SYNDATATOOLBOX_API AActorTarget : public AActor
{
	GENERATED_BODY()

public:
	AActorTarget();

	UPROPERTY()
		UStaticMeshComponent* Mesh;

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:
	// Called every frame
	virtual void Tick(float DeltaTime) override;
};