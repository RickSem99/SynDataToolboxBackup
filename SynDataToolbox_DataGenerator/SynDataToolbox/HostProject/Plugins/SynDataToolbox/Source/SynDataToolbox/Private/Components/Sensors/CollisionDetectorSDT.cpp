// Fill out your copyright notice in the Description page of Project Settings.


#include "Components/Sensors/CollisionDetectorSDT.h"

// Sets default values
ACollisionDetectorSDT::ACollisionDetectorSDT()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = enableIndependentTick;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	ActorHit = nullptr;
	bIsBusy = false;
}

// Called when the game starts or when spawned
void ACollisionDetectorSDT::BeginPlay()
{
	Super::BeginPlay();
	InitSensor();

	if (TimeSampling != 0.0f) {
		SetTickMode(false); //do not tick!
		FTimerHandle ObservationTimerHandle;
		GetWorld()->GetTimerManager().SetTimer(ObservationTimerHandle, this, &ACollisionDetectorSDT::TakePeriodicObs, TimeSampling, true, 0.0f);
	}

}

void ACollisionDetectorSDT::TakePeriodicObs()
{
	TakeObs();
}

// Called every frame
void ACollisionDetectorSDT::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	if (TimeSampling == 0.0f && !bEnvStep) {
		TakeObs();
	}
}

const FString ACollisionDetectorSDT::GetSensorName()
{
	return "CollisionDetector("+GetActorLabel() + ")";
}

const FString ACollisionDetectorSDT::GetSensorSetup()
{
	return "{PawnAgent:" + CastedPawnAgent->GetActionManagerName() + ","
		+ "ActorTarget:" + ActorTarget->GetActorLabel() + "}";
}

const uint32 ACollisionDetectorSDT::GetObservationSize()
{
	return 1;
}

const bool ACollisionDetectorSDT::InitSensor()
{
	bool ErrorInit = false;

	if (PawnAgent) {
		CastedPawnAgent = Cast<IActionManagerSDT>(PawnAgent);
		if (!CastedPawnAgent) {
			ErrorInit = true;
		}
		else {
			ActorHit = CastedPawnAgent->GetHitHandler();
			LastObservation = new uint8[GetObservationSize()];
		}
	}
	else {
		ErrorInit = true;
	}
	if (!ActorTarget) {
		ErrorInit = true;
	}
	if (ErrorInit && GEngine) {
		GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Red, TEXT("ERROR PAWN AGENT ACTOR TARGET"));
	}

	return !ErrorInit;
}

const bool ACollisionDetectorSDT::ChangeSensorSettings(const TArray<FString>& Settings)
{
	if (Settings.Num() != 0) 
	{
	//if (Settings.Num()  == 2)
	//{
	//	//change PawnAgent and ActorTarget
	//	PawnAgent = 
	//}
	//else if (Settings.Num() == 1)
	//{ 
	//	//change PawnAgent

	//}
		UE_LOG(LogTemp, Error, TEXT("Invalid Settings."))
		return false;
	}
	return true;
}

const bool ACollisionDetectorSDT::GetLastObs(uint8* Buffer)
{
	while(bIsBusy){}
	if (LastObservation != nullptr) 
	{
		if (bEnvStep) {
			TakeObs();
		}
		bIsBusy = true;
		memcpy(Buffer, LastObservation, GetObservationSize());
		bIsBusy = false;
		return true;
	}
	return false;
}

const bool ACollisionDetectorSDT::TakeObs()
{
	while(bIsBusy){}
	if (ActorHit->bBlockingHit) {
		FString Label = ActorHit->GetActor()->GetActorLabel();
		if (Label.Equals(ActorTarget->GetActorLabel())) {
			HasCollided = 1;
			UE_LOG(LogTemp, Warning, TEXT("Target"))
			bIsBusy = true;
			LastObservation[0] = 1;
			bIsBusy = false;
			return true;
		}
	}
	bIsBusy = true;
	LastObservation[0] = 0;
	bIsBusy = false;
	HasCollided = 0;
	LastObservationTimestamp = FDateTime::Now().ToString();
	return true;
}

const void ACollisionDetectorSDT::SetTickMode(bool Value)
{
	enableIndependentTick = Value;
	PrimaryActorTick.bCanEverTick = enableIndependentTick;
}
