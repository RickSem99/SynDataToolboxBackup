# include "Components/ResetManagers/MazeResetManagerSDT.h"
# include <Misc/OutputDeviceNull.h>


AMazeResetManagerSDT::AMazeResetManagerSDT()
{
	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = false;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMeshComponent"));
	ActorsToSpawn = TArray<AActor*>();
	ActorHit = new FHitResult();
	FMath::SRandInit(10000);
}

void AMazeResetManagerSDT::BeginPlay() {
	Super::BeginPlay();

	
	if (!CheckInitSettings() && GEngine) {
		FString Text = "ResetManager " + GetResetManagerName() + ":Invalid Init Settings. Check definitions. Note that ActorsToSpawn Actors must have 'movable' setting. Check it (below location and rotation, in 'details' panel). Check flags in MazeCreator!";
		const TCHAR* TText = *Text;
		GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Red, TText);
		UE_LOG(LogTemp, Error, TEXT("%s"), TText)
	}

	// ONLY FOR DEBUG
	//FTimerHandle ObservationTimerHandle;
	//GetWorld()->GetTimerManager().SetTimer(ObservationTimerHandle, this, &AMazeResetManagerSDT::Reset, 3.0f, true);

}

bool AMazeResetManagerSDT::CheckInitSettings()
{
	//check if Maze
	if (MazeManager->GetClass()->GetName().Contains(TEXT("MazeCreator"))) {
		if (PawnAgent && ActorTarget) {
			PawnAgentCasted = Cast<IActionManagerSDT>(PawnAgent);
			ActorTargetCasted = Cast<AActorTarget>(ActorTarget);
			if (PawnAgentCasted && ActorTargetCasted) {
				//everything ok fill class parameters
				MazeOriginLocation = MazeManager->GetActorLocation();
				FIntProperty* MazeWidthSizeProperty = FindFProperty<FIntProperty>(MazeManager->GetClass(), TEXT("Maze Width"));
				MazeWidth = MazeWidthSizeProperty->GetPropertyValue_InContainer(MazeManager);
				FIntProperty* MazeHeightSizeProperty = FindFProperty<FIntProperty>(MazeManager->GetClass(), TEXT("Maze Height"));
				MazeHeight = MazeHeightSizeProperty->GetPropertyValue_InContainer(MazeManager);
				
				//check info like "CustomSeed" whether is True or not. Probably is
				FBoolProperty* MazeCustomSeedProperty = FindFProperty<FBoolProperty>(MazeManager->GetClass(), TEXT("Use Custom Maze Seed?"));
				if (MazeCustomSeedProperty->GetPropertyValue_InContainer(MazeManager)) {
					return true;
				}
			}
		}
	}
	return false;

}

// TODO: Will be removed. Only for debugging
void AMazeResetManagerSDT::Reset() {
	TArray<FString> ciao = { "" };
	PerformReset(ciao);
}


const bool AMazeResetManagerSDT::PerformReset(TArray<FString>& FieldArray)
{
	//FIRST OF ALL, REGENERATE MAZE With New Seed
	if (bRegenerateMaze) {
		FIntProperty* MazeCustomSeedProperty = FindFProperty<FIntProperty>(MazeManager->GetClass(), TEXT("Maze Seed"));
		MazeCustomSeedProperty->SetPropertyValue_InContainer(MazeManager, FMath::SRand() * 1000);

		FOutputDeviceNull ar;
		const FString command = FString::Printf(TEXT("GenMaze"));
		MazeManager->CallFunctionByNameWithArguments(*command, ar, NULL, true);

	}

	bool FoundPawnPosition = false;
	bool FoundActorPosition = false;
	FRotator Rot = FRotator();
	float XPos = 0.0;
	float YPos = 0.0;
	float ZPos = MazeOriginLocation.Z;

	while (!FoundPawnPosition) {
		int WCell = FMath::Rand() % MazeWidth;
		int HCell = FMath::Rand() % MazeHeight;
		XPos = MazeOriginLocation.X + FloorMeshWidth * (WCell - 1) + FloorMeshWidth / 2;
		YPos = MazeOriginLocation.Y + FloorMeshHeight * (HCell - 1) + FloorMeshHeight / 2;
		Rot.Yaw = FMath::RandRange(-180.0, 180.0);

		PawnAgent->SetActorLocation(FVector(XPos, YPos, ZPos+1), false); //without collision initially
		PawnAgent->SetActorLocation(FVector(XPos, YPos, ZPos-2), true, ActorHit); //collision
		//devo verificare prima cose
		if (ActorHit->bBlockingHit && ActorHit->GetActor() == MazeManager) {
			PawnAgent->SetActorLocationAndRotation(FVector(XPos, YPos, ZPos + 2), Rot, true, ActorHit);
			if (!ActorHit->bBlockingHit) {
				FoundPawnPosition = true;
			}
		}
	}
	//when code exits from do-while, i found correct location!
	PawnAgentCasted->ResetPhysics();

	//move actor target
	while (!FoundActorPosition) {
		int WCell = FMath::Rand() % MazeWidth;
		int HCell = FMath::Rand() % MazeHeight;
		XPos = MazeOriginLocation.X + FloorMeshWidth * (WCell - 1) + FloorMeshWidth / 2;
		YPos = MazeOriginLocation.Y + FloorMeshHeight * (HCell - 1) + FloorMeshHeight / 2;
		Rot.Yaw = FMath::RandRange(-180.0, 180.0);

		ActorTarget->SetActorLocation(FVector(XPos, YPos, MazeOriginLocation.Z+1)); //without collision initially
		ActorTarget->SetActorLocation(FVector(XPos, YPos, MazeOriginLocation.Z -2), true, ActorHit); //collision
		//devo verificare prima cose
		if (ActorHit->bBlockingHit && ActorHit->GetActor() == MazeManager) {
			ActorTarget->SetActorLocation(FVector(XPos, YPos, MazeOriginLocation.Z + 2), true, ActorHit);
			if (!ActorHit->bBlockingHit) {
				FoundActorPosition = true;
			}
		}
	}

	//Move ActorsToSpawn Actors!
	for (AActor* ActorToSpawn : ActorsToSpawn)
	{
		bool FoundPosition = false;
		while (!FoundPosition)
		{
	
			int WCell = FMath::Rand() % MazeWidth;
			int HCell = FMath::Rand() % MazeHeight;
			XPos = MazeOriginLocation.X + FloorMeshWidth * (WCell - 1) + FloorMeshWidth / 2;
			YPos = MazeOriginLocation.Y + FloorMeshHeight * (HCell - 1) + FloorMeshHeight / 2;
			Rot.Yaw = FMath::RandRange(-180.0, 180.0);

			ActorToSpawn->SetActorLocation(FVector(XPos, YPos, MazeOriginLocation.Z + 1)); //without collision initially, for "casper spawning" between grounds
			ActorToSpawn->SetActorLocation(FVector(XPos, YPos, MazeOriginLocation.Z - 2), true, ActorHit); //collision
			if (ActorHit->bBlockingHit && ActorHit->GetActor() == MazeManager) {
				ActorToSpawn->SetActorLocationAndRotation(FVector(XPos, YPos, MazeOriginLocation.Z + 2), Rot, true, ActorHit);
				if (!ActorHit->bBlockingHit) {
					FoundPosition = true;
				}
			}
		}
	}


	return true;
}

const bool AMazeResetManagerSDT::ChangeResetSettings(const TArray<FString>& Settings)
{
	if (Settings.Num() == 0)
	{
		return true;
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Invalid Settings."))
			return false;
	}
}

const FString AMazeResetManagerSDT::GetResetManagerName() const
{
	return "MazeResetManager(" + GetActorLabel() + ")";
}

void AMazeResetManagerSDT::Tick(float DeltaTime) {
	Super::Tick(DeltaTime);
	//Do nothing
}