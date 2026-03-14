// Fill out your copyright notice in the Description page of Project Settings.
#include "Components/ActionManagers/ControlledActionManagerSDT.h"

// Sets default values
AControlledActionManagerSDT::AControlledActionManagerSDT()
{
	// Set this pawn to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true; // for physics solver

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

}

// Called when the game starts or when spawned
void AControlledActionManagerSDT::BeginPlay()
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
	UUniformPhysicsManagerSDT* PhysicsObject = NewObject<UUniformPhysicsManagerSDT>();
	UProportionalPIDManagerSDT* PIDObject = NewObject<UProportionalPIDManagerSDT>();
	PIDRegulator.SetObject(PIDObject);
	PIDRegulator.SetInterface(Cast<IPIDManagerSDT>(PIDObject));
	PhysicsSolver.SetObject(PhysicsObject);
	PhysicsSolver.SetInterface(Cast<IPhysicsManagerSDT>(PhysicsObject));
	CurrentPhysicsManager = PhysicsSolver->GetPhysicsManagerName();
	CurrentPIDManager = PIDRegulator->GetPIDManagerName();


	//Set up control and physics settings
	PhysicsSolver->GetActorReference(this, GetHitHandler());
	PIDRegulator->SetNumControlledVariables(2);
	PIDRegulator->SetParameters({ 2,2 }); //TBD About Parameters Value
	PhysicsSolver->SetPhysicsSettings({
		AgentMass,AgentLength,AgentWidth,
		FrictionParameter, AngularFrictionParameter,
		MAX_FORCE, MAX_MOMENTUM, MIN_FORCE, MIN_MOMENTUM
		});

	//////init Position and Rotation vector
	//CurrentPosition = GetActorLocation();
	//OldPosition = CurrentPosition;
	//CurrentRotation = GetActorRotation();
	//CurrentRotation.Normalize();
	//OldRotation = CurrentRotation;
}

// Called every frame
void AControlledActionManagerSDT::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	//compute "physics" only if SetPoints are defined
	if (AgentMass != 0 && AgentLength != 0 && AgentWidth != 0) {
		PIDComputation(DeltaTime);
	}
}

//compute new position and Rotation of ControlledActionManager
const int8_t AControlledActionManagerSDT::PIDComputation(float DeltaTime) {

	/*Linear Velocity*/
	//FVector CurrentVelocity = (1 - FrictionParameter) * (GetActorLocation() - OldPosition);
	//* | is dot symbol for dot product between two vectors*/
	//float CurrentVelocityForward = CurrentVelocity | GetActorForwardVector();
	//float IdealAcceleration = TargetLinearVelocity - CurrentVelocityForward;
	//float ActualForce = IdealAcceleration * AgentMass;
	//float AuxNextAcceleration = fmin(ActualForce / AgentMass, MAX_FORCE / AgentMass);
	//CurrentLinearAcceleration = fmax(AuxNextAcceleration, MIN_FORCE / AgentMass);
	//FVector NextAccelerationVector = (CurrentLinearAcceleration * GetActorForwardVector());
	////Update positions
	//OldPosition = CurrentPosition;
	//CurrentPosition = OldPosition + CurrentVelocity + NextAccelerationVector;
	//	
	//*Angular Velocity*/
	////in this case we need to mantain values between 0 and 360 (?)
	//FRotator RotatorYaw = FRotator(); //pitch, yaw, roll
	//RotatorYaw.Yaw = 1.0f;
	//float TargetAngularVelocityDeg = (TargetAngularVelocity * 180) / PI; //rotators works with degrees and not radians
	//FRotator TargetAngularVelocityRotator = RotatorYaw * TargetAngularVelocityDeg;
	//FRotator CurrentAngularVelocityRotator = (1 - AngularFrictionParameter) * (CurrentRotation - OldRotation);
	//float IdealAngularAcceleration = TargetAngularVelocityRotator.Yaw - CurrentAngularVelocityRotator.Yaw;
	//float ActualMomentumAngularAcceleration = ((pow(AgentWidth, 2) + pow(AgentLength, 2)) * AgentMass * IdealAngularAcceleration) / 12;
	//float AuxNextAngularAcceleration = fmin(MAX_MOMENTUM / AgentMass, ActualMomentumAngularAcceleration / AgentMass);
	//float NextAngularAcceleration = fmax(MIN_MOMENTUM / AgentMass, AuxNextAngularAcceleration);
	//FRotator NextAccelerationRotator = RotatorYaw * NextAngularAcceleration;
	//CurrentAngularAcceleration = (NextAccelerationRotator.Yaw * PI) / 180;
	//OldRotation = CurrentRotation;
	//CurrentRotation = (OldRotation + CurrentAngularVelocityRotator + NextAccelerationRotator); //regularization
	//SetActorLocationAndRotation(CurrentPosition, CurrentRotation, true, ActorHit);
	//CurrentLinearVelocity = (CurrentPosition - OldPosition) | GetActorForwardVector();
	//CurrentAngularVelocity = ((CurrentRotation - OldRotation).Yaw * PI) / 180;

	//New Control Chain
	dt = DeltaTime;
	CurrentValues = PhysicsSolver->GetCurrentOutputs();
	PIDRegulator->SetError({ TargetLinearVelocity * DeltaTime * LinearMultiplexFactor - CurrentValues[0], TargetAngularVelocity * DeltaTime * AngularMultiplexFactor - CurrentValues[2] });
	TArray<float> Corrections = PIDRegulator->GetCorrection();
	CurrentValues = PhysicsSolver->Compute(Corrections);
	//update informations to display in details panel
	CurrentLinearVelocity = CurrentValues[0] / (DeltaTime * LinearMultiplexFactor);
	CurrentAngularVelocity = CurrentValues[2] / (DeltaTime * AngularMultiplexFactor);
	CurrentLinearAcceleration = CurrentValues[1] / (LinearMultiplexFactor * DeltaTime);
	CurrentAngularAcceleration = CurrentValues[3] / (AngularMultiplexFactor * DeltaTime);

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

void AControlledActionManagerSDT::ResetPhysics() {

	PhysicsSolver->Reset();
	bCollision = false;
	TargetLinearVelocity = 0.0;
	TargetAngularVelocity = 0.0;

}

const FString AControlledActionManagerSDT::GetActionManagerName() const
{
	return "ControlledActionManager(" + GetActorLabel() + ")";
}

const FString AControlledActionManagerSDT::GetActionManagerSetup() const
{
	return "UPDATESETPOINTS@{AgentMass:" + FString::SanitizeFloat(AgentMass) + ",AgentLength:" + FString::SanitizeFloat(AgentLength) + ",AgentWidth:" + FString::SanitizeFloat(AgentWidth) + ",FrictionParameter:" + FString::SanitizeFloat(FrictionParameter) +
		+",AngularFrictionParameter:" + FString::SanitizeFloat(AngularFrictionParameter) + "}";
}

const bool AControlledActionManagerSDT::InitSettings(const TArray<FString>& Settings)
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

const int8_t AControlledActionManagerSDT::PerformAction(TArray<FString>& Action)
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

int8_t AControlledActionManagerSDT::ChangeSetPoints(TArray<FString>& ActionSettings)
{
	if (ActionSettings.Num() != 2) {
		UE_LOG(LogTemp, Error, TEXT("ARGUMENT ERROR: 2 needed (v, omega) but %i given"), ActionSettings.Num())

	}
	if (!bCollision) {
		TargetLinearVelocity = FCString::Atof(*ActionSettings[0]);
		TargetAngularVelocity = FCString::Atof(*ActionSettings[1]);
	}
	if (PIDComputation(dt)) {

		return 1;
	}
	return 0;
}

const int AControlledActionManagerSDT::ActionToID(const FString& Action) const
{
	if (Action == "UPDATESETPOINTS") return UPDATESETPOINTS;
	else return UNKNOWN;
}

void AControlledActionManagerSDT::Possess()
{
	UE_LOG(LogTemp, Warning, TEXT("Controlling: %s"), *GetActionManagerName())
		GetWorld()->GetFirstPlayerController()->Possess(this);
}

void AControlledActionManagerSDT::UnPossess()
{
	GetWorld()->GetFirstPlayerController()->UnPossess();
}

// Called to bind functionality to input
void AControlledActionManagerSDT::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	//do nothing in this case
}

FHitResult* AControlledActionManagerSDT::GetHitHandler()
{
	return ActorHit;
}

