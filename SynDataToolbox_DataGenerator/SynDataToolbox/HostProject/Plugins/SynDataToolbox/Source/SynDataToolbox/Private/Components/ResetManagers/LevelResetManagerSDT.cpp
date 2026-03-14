// Fill out your copyright notice in the Description page of Project Settings.
#include "Components/ResetManagers/LevelResetManagerSDT.h"

//There are some MAGIC NUMBERS to remove. In fact i can do something like "cruise control"


// Sets default values
ALevelResetManagerSDT::ALevelResetManagerSDT()
{
 	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = false;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMeshComponent"));
	ActorsToSpawn = TArray<AActor*>();
	ActorHit = new FHitResult();
}

// Called every frame
void ALevelResetManagerSDT::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	//do nothing. Tick is disabled
}

// TODO: Will be removed. Only for debugging
void ALevelResetManagerSDT::Reset() {
	TArray<FString> ciao = { "" };
	PerformReset(ciao );
}

// Called when the game starts or when spawned
void ALevelResetManagerSDT::BeginPlay()
{
	Super::BeginPlay();
	
	// ONLY FOR DEBUG
	/*FTimerHandle ObservationTimerHandle;
	GetWorld()->GetTimerManager().SetTimer(ObservationTimerHandle, this, &ALevelResetManagerSDT::Reset, 3.0f, true);
	*/
	//INIT Arrays XMAX, XMIN YMAX,YMIN AND Z
	for (FString name : FloorNames) {
		ZFloors.Add(name, NAN);
	}

	if (!CheckInitSettings() && GEngine) {
		FString Text = "ResetManager " + GetResetManagerName() + ":Invalid Init Settings. Check definitions. Note that ActorsToSpawn Actors must have 'movable' setting. Check it (below location and rotation, in 'details' panel)";
		const TCHAR* TText = *Text;
		GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Red, TText);
		UE_LOG(LogTemp,Error,TEXT("%s"), TText)
	}
}

//check casting objects and set Zfloor
bool ALevelResetManagerSDT::CheckInitSettings()
{
	if (PawnAgent && ActorTarget) {
		PawnAgentCasted = Cast<IActionManagerSDT>(PawnAgent);
		ActorTargetCasted = Cast<AActorTarget>(ActorTarget);
		if (PawnAgentCasted && ActorTargetCasted) {
			//check for floor now
			for (TActorIterator<AActor> ActorItr(GetWorld()); ActorItr; ++ActorItr)
			{
				FString ClassFloor = ParseClassName(ActorItr->GetActorLabel());
				float* ReturnValue = ZFloors.Find(ClassFloor);
				
				if (ReturnValue)
				{
					float ZFloor = *ReturnValue;
					if (isnan(ZFloor))
					{
						//found at least one floor for specific class name
						ZFloors.Add(ClassFloor, ActorItr->GetActorLocation().Z);
					}

					//update X,Y,ranges
					float XFloor = ActorItr->GetActorLocation().X;
					float YFloor = ActorItr->GetActorLocation().Y;

					float* XMaxFloor = XMaxFloors.Find(ClassFloor);
					if (XMaxFloor) {
						if (XFloor > *XMaxFloor) {
							XMaxFloors.Add(ClassFloor, XFloor);
						}
					}
					else {
						XMaxFloors.Add(ClassFloor, XFloor);
					}

					float* XMinFloor = XMinFloors.Find(ClassFloor);
					if (XMinFloor){
						if (XFloor <= *XMinFloor) {
							XMinFloors.Add(ClassFloor, XFloor);
						}
					}
					else {
						XMinFloors.Add(ClassFloor, XFloor);
					}

					float* YMaxFloor = YMaxFloors.Find(ClassFloor);
					if (YMaxFloor){
						if (YFloor > *YMaxFloor) {
							YMaxFloors.Add(ClassFloor, YFloor);
						}
					}
					else {
						YMaxFloors.Add(ClassFloor, YFloor);
					}

					float* YMinFloor = YMinFloors.Find(ClassFloor);
					if (YMinFloor) {
						if (YFloor <= *YMinFloor) {
							YMinFloors.Add(ClassFloor, YFloor);
						}
					}
					else {
						YMinFloors.Add(ClassFloor, YFloor);
					}
				}
			}
			
			bool Check = true;
			for (FString Name : FloorNames)
			{
				if (Check) {
					float* YMinFloor = YMinFloors.Find(Name);
					float* YMaxFloor = YMaxFloors.Find(Name);
					float* XMinFloor = XMinFloors.Find(Name);
					float* XMaxFloor = XMaxFloors.Find(Name);
					
					if (YMinFloor && YMaxFloor && XMinFloor && XMaxFloor) {
						Check = true;
					}
				}
			}

			if (Check == true) 
			{
				bool Mobility = true;
				//check mobility of ActorsToSpawn
				for (AActor* ActorToSpawn : ActorsToSpawn)
				{
					if (Mobility) {
						Mobility = ActorToSpawn->IsRootComponentMovable();
					}
				}
				return true && Mobility;
			}
			//otherwise at least one FloorName Incorrect!
		}
	}
	return false;
}

FString ALevelResetManagerSDT::ParseClassName(FString String)
{
	TArray<FString> ParsedString;
	String.ParseIntoArray(ParsedString, TEXT("_"), true);
	return ParsedString[0];
}

const FString ALevelResetManagerSDT::GetResetManagerName() const
{
	return "LevelResetManager("+GetActorLabel()+ ")";
}

const bool ALevelResetManagerSDT::PerformReset(TArray<FString>& FieldArray)
{

	//MOVE PAWNAGENT
	float XPos = 0.0;
	float YPos = 0.0;
	float ZPos = 0.0;
	FRotator Rot;
	FString Name = "";
	int Index = 0;
	bool FoundPawnPosition = false;
	bool FoundActorPosition = false;

	while (!FoundPawnPosition) {
		Index = FMath::Rand() % ZFloors.Num();
		Name = FloorNames[Index];
		XPos = FMath::RandRange(*XMinFloors.Find(Name), *XMaxFloors.Find(Name));
		YPos = FMath::RandRange(*YMinFloors.Find(Name), *YMaxFloors.Find(Name));
		ZPos = *ZFloors.Find(Name);

		Rot = PawnAgent->GetActorRotation();
			Rot.Yaw = FMath::RandRange(0.0, 360.0);

		PawnAgent->SetActorLocation(FVector(XPos, YPos, ZPos),false); //without collision initially
		PawnAgent->SetActorLocation(FVector(XPos, YPos, ZPos-3),true,ActorHit); //collision
		if (ActorHit->bBlockingHit) {
			if (ActorHit->GetActor()) {
				FString Label = ActorHit->GetActor()->GetActorLabel();
				if (Label.Equals(Name)) {
					PawnAgent->SetActorLocationAndRotation(FVector(XPos, YPos, ZPos +2),Rot,true,ActorHit);
					if (!ActorHit->bBlockingHit) {
						FoundPawnPosition = true;
					}
				}
			}
		}
	}

	//when code exits from do-while, i found correct location!
	PawnAgentCasted->ResetPhysics();

	//move actor target
	while (!FoundActorPosition) {
		Index = FMath::Rand() % ZFloors.Num();
		Name = FloorNames[Index];
		XPos = FMath::RandRange(*XMinFloors.Find(Name), *XMaxFloors.Find(Name));
		YPos = FMath::RandRange(*YMinFloors.Find(Name), *YMaxFloors.Find(Name));
		ZPos = *ZFloors.Find(Name);

		ActorTarget->SetActorLocation(FVector(XPos, YPos, ZPos)); //without collision initially
		ActorTarget->SetActorLocation(FVector(XPos, YPos, ZPos-3), true, ActorHit); //collision
		if (ActorHit->bBlockingHit) {
			if (ActorHit->GetActor()) {
				FString Label = ActorHit->GetActor()->GetActorLabel();
				if (Label.Equals(Name)) {
					FoundActorPosition = true;
				}
			}
		}
	}
	ActorTarget->SetActorLocation(FVector(XPos, YPos, ZPos+2), true, ActorHit);

	//Move ActorsToSpawn Actors!
	for (AActor* ActorToSpawn : ActorsToSpawn)
	{
		bool FoundPosition = false;
		while (!FoundPosition)
		{
			Index = FMath::Rand() % ZFloors.Num();
			Name = FloorNames[Index];
			XPos = FMath::RandRange(*XMinFloors.Find(Name), *XMaxFloors.Find(Name));
			YPos = FMath::RandRange(*YMinFloors.Find(Name), *YMaxFloors.Find(Name));
			ZPos = *ZFloors.Find(Name);

			
			Rot = ActorToSpawn->GetActorRotation();
			Rot.Yaw = FMath::RandRange(0.0, 360.0);

			ActorToSpawn->SetActorLocation(FVector(XPos, YPos, ZPos)); //without collision initially, for "casper spawning" between grounds
			ActorToSpawn->SetActorLocation(FVector(XPos, YPos, ZPos - 3), true, ActorHit); //collision
			if (ActorHit->bBlockingHit) {
				if (ActorHit->GetActor()) {
					FString Label = ActorHit->GetActor()->GetActorLabel();
					if (Label.Equals(Name)) {
						ActorToSpawn->SetActorLocationAndRotation(FVector(XPos, YPos, ZPos + 2), Rot, true, ActorHit);
						if (!ActorHit->bBlockingHit) {
							FoundPosition = true;
						}
					}
				}
			}
		}
	}


	return true;
}

const bool ALevelResetManagerSDT::ChangeResetSettings(const TArray<FString>& Settings )
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