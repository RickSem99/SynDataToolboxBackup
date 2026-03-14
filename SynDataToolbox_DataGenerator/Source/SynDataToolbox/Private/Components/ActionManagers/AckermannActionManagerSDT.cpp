// Fill out your copyright notice in the Description page of Project Settings.
#include "Components/ActionManagers/AckermannActionManagerSDT.h"

// Sets default values
AAckermannActionManagerSDT::AAckermannActionManagerSDT()
{
 	// Tick() is not called every frame but synchronously with the env_step or perform_action command.
	PrimaryActorTick.bCanEverTick = false; // for physics solver

	//Actor structure
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMeshComponent"));
	CameraSpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArmComponent"));
	CameraComponent = CreateDefaultSubobject<UCameraComponent>(TEXT("CameraComponent"));
	SetRootComponent(Mesh);
	ConstructorHelpers::FObjectFinder<UStaticMesh> StaticMeshAsset(TEXT("/SynDataToolbox/AGVMesh"));
	Mesh->SetStaticMesh(StaticMeshAsset.Object);
	Mesh->SetRelativeScale3D(FVector(0.6f, 0.6f, 0.6f));
	CameraSpringArm->SetupAttachment(Mesh);
	CameraComponent->SetupAttachment(CameraSpringArm);
	CameraSpringArm->SetRelativeLocationAndRotation(FVector(0.0f, 0.0f, 50.0f), FRotator(-45.0f, 0.0f, 0.0f));
	CameraSpringArm->TargetArmLength = 300.f;


	// Create hit
	ActorHit = new FHitResult();	// Initialize the hit info object
	CurrentValues = TArray<float>();
	
	CurrentVel = TArray<float>();
	CurrentVel.Add(0.0);  // v
	CurrentVel.Add(0.0);  // w
}

// Called when the game starts or when spawned
void AAckermannActionManagerSDT::BeginPlay()
{
	Super::BeginPlay();
	if (GEngine && AgentMass == 0.0f)
	{
		GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Red, TEXT("UNSET AGENT MASS!"));
	}
	if (GEngine && (FrictionParameter > 1 || FrictionParameter < 0))
	{
		GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Red, TEXT("INVALID FRICTION PARAMETER!"));
	}	if (GEngine && (AngularFrictionParameter > 1 || AngularFrictionParameter < 0))
	{
		GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Red, TEXT("INVALID ANGULAR FRICTION PARAMETER!"));
	}

	//Physiscs and Controller
	UAckermannPhysicsManagerSDT* PhysicsObject = NewObject<UAckermannPhysicsManagerSDT>();
	PhysicsSolver.SetObject(PhysicsObject);
	PhysicsSolver.SetInterface(Cast<IPhysicsManagerSDT>(PhysicsObject));
	CurrentPhysicsManager = PhysicsSolver->GetPhysicsManagerName();

	/*
	UProportionalPIDManagerSDT* PIDObject = NewObject<UProportionalPIDManagerSDT>();
	PIDRegulator.SetObject(PIDObject);
	PIDRegulator.SetInterface(Cast<IPIDManagerSDT>(PIDObject));
	CurrentPIDManager = PIDRegulator->GetPIDManagerName();
	PIDRegulator->SetNumControlledVariables(2);
	PIDRegulator->SetParameters({2,2}); //TBD About Parameters Value
	*/

	PhysicsSolver->GetActorReference(this, GetHitHandler());
	PhysicsSolver->SetPhysicsSettings({
		AgentMass,AgentLength,AgentWidth,
		FrictionParameter, AngularFrictionParameter,
		MAX_FORCE, MAX_MOMENTUM, MIN_FORCE, MIN_MOMENTUM, isRotAngle
	});

	//////init Position and Rotation vector
	//CurrentPosition = GetActorLocation();
	//OldPosition = CurrentPosition;
	//CurrentRotation = GetActorRotation();
	//CurrentRotation.Normalize();
	//OldRotation = CurrentRotation;
}

// Called every frame
void AAckermannActionManagerSDT::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	// this is not needed anymore since we want to update the vehicle state everytime the env_step command is performed.
	/*
	if (AgentMass != 0 && AgentLength!=0 && AgentWidth!=0 ) {
		PIDComputation(DeltaTime);
	}
	*/
}

//compute new position and Rotation of AckermannActionManager
const int8_t AAckermannActionManagerSDT::PositionComputation(float DeltaTime) {
	PhysicsSolver->SetNewPosition(CurrentVel, DeltaTime, isRotAngle);

	if (ActorHit->bBlockingHit) {
		UE_LOG(LogTemp, Error, TEXT("Collision"))
		bCollision = true;
		CurrentAngularAcceleration = 0.0;
		CurrentAngularVelocity = 0.0;
		CurrentLinearVelocity = 0.0;
		CurrentLinearAcceleration = 0.0;
	}
	return bCollision;
}

void AAckermannActionManagerSDT::ResetPhysics() {

	PhysicsSolver->Reset();
	bCollision = false;
	TargetLinearVelocity = 0.0;
	TargetAngularVelocity = 0.0;

}

const FString AAckermannActionManagerSDT::GetActionManagerName() const
{
	return "AckermannActionManager("+GetActorLabel() + ")";
}

const FString AAckermannActionManagerSDT::GetActionManagerSetup() const
{
	return "UPDATESETPOINTS@{AgentMass:" + FString::SanitizeFloat(AgentMass) + ",AgentLength:"+ FString::SanitizeFloat(AgentLength) +",AgentWidth:"+ FString::SanitizeFloat(AgentWidth) +",FrictionParameter:"+ FString::SanitizeFloat(FrictionParameter) +
		+",AngularFrictionParameter:" + FString::SanitizeFloat(AngularFrictionParameter)+"}";
}

const bool AAckermannActionManagerSDT::InitSettings(const TArray<FString>& Settings)
{
	if ((Settings.Num() == 0))
	{
		return true;
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("Invalid Settings."));
		return false;
	}
	//TODO: Change settings instead, when is possible to define mass and other stuffs!
}

const int8_t AAckermannActionManagerSDT::PerformAction(TArray<FString>& Action)
{
	// are given 2 values, the first one is for linear velocity, the last one is for angular velocity
	int8_t PerformActionCode;

	FString ActionName = Action[0];
	
	Action.RemoveAt(0);

	const int ActionID = ActionToID(ActionName);

	switch (ActionID)
	{
		case UPDATESETPOINTS:
		{
			PerformActionCode = ChangeSetPoints(Action);
		} break;
		default:
		{
			PerformActionCode = -1;
			UE_LOG(LogTemp, Error, TEXT("Unknown action: %s"), *ActionName);
		} break;
	}

	return PerformActionCode;
}

int8_t AAckermannActionManagerSDT::ChangeSetPoints(TArray<FString>& ActionSettings)
{
	if (ActionSettings.Num() != 3) {
		UE_LOG(LogTemp, Error, TEXT("ARGUMENT ERROR: 3 needed (v, omega, dt) but %i given"), ActionSettings.Num())	
	}

	if (!bCollision) {
		TargetLinearVelocity = FCString::Atof(*ActionSettings[0]);
		TargetAngularVelocity = FCString::Atof(*ActionSettings[1]);
		dt = FCString::Atof(*ActionSettings[2]);
	}

	CurrentVel[0] = TargetLinearVelocity;
	CurrentVel[1] = TargetAngularVelocity;

	if (PositionComputation(dt)) {
		
		return 1;
	}
	return 0;
}

const int AAckermannActionManagerSDT::ActionToID(const FString& Action) const
{
	if (Action == "UPDATESETPOINTS") return UPDATESETPOINTS;
	else return UNKNOWN;
}

void AAckermannActionManagerSDT::Possess()
{
	UE_LOG(LogTemp, Warning, TEXT("Controlling: %s"), *GetActionManagerName())
		GetWorld()->GetFirstPlayerController()->Possess(this);
}

void AAckermannActionManagerSDT::UnPossess()
{
	GetWorld()->GetFirstPlayerController()->UnPossess();
}

// Called to bind functionality to input
void AAckermannActionManagerSDT::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	//do nothing in this case
}

FHitResult* AAckermannActionManagerSDT::GetHitHandler()
{
	return ActorHit;
}


