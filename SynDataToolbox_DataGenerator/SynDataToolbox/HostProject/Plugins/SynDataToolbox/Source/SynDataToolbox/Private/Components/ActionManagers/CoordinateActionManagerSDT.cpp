#include "Components/ActionManagers/CoordinateActionManagerSDT.h" 
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

ACoordinateActionManagerSDT::ACoordinateActionManagerSDT()
{
	PrimaryActorTick.bCanEverTick = false;

	// 1. Mesh Base
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	SetRootComponent(Mesh);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> StaticMeshAsset(TEXT("/SynDataToolbox/CoordinateActionManagerMesh"));
	if (StaticMeshAsset.Succeeded())
	{
		Mesh->SetStaticMesh(StaticMeshAsset.Object);
		Mesh->SetRelativeScale3D(FVector(0.5f, 0.5f, 0.5f));
	}

	// 2. SpringArm
	CameraSpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArmComponent"));
	CameraSpringArm->SetupAttachment(Mesh);
	CameraSpringArm->SetRelativeLocationAndRotation(FVector(0.0f, 0.0f, 50.0f), FRotator(0.0f, 0.0f, 0.0f));
	CameraSpringArm->TargetArmLength = 0.f;
	// =========================================================================

	// 3. Camera
	CameraComponent = CreateDefaultSubobject<UCameraComponent>(TEXT("CameraComponent"));
	CameraComponent->SetupAttachment(CameraSpringArm);

	// 4. LUCE SOLIDALE
	SpotLightComponent = CreateDefaultSubobject<USpotLightComponent>(TEXT("SpotLight"));
	SpotLightComponent->SetupAttachment(CameraComponent);

	// Configurazioni di default
	SpotLightComponent->SetIntensity(5000.0f);
	SpotLightComponent->SetOuterConeAngle(44.0f);
	SpotLightComponent->SetInnerConeAngle(10.0f);
	SpotLightComponent->SetAttenuationRadius(1000.0f);
	SpotLightComponent->SetLightColor(FLinearColor::White);
	SpotLightComponent->SetRelativeRotation(FRotator::ZeroRotator);

	ActorHit = new FHitResult();
}

const FString ACoordinateActionManagerSDT::GetActionManagerName() const
{
	return "CoordinateActionManager(" + GetActorLabel() + ")";
}

const FString ACoordinateActionManagerSDT::GetActionManagerSetup() const
{
	return FString("MOVETO,GETPOS@{}");
}

const int ACoordinateActionManagerSDT::ActionToID(const FString& Action) const
{
	if (Action == "MOVETO") return MOVETO;
	else if (Action == "GETPOS") return GETPOS;
	else return UNKNOWN;
}

const bool ACoordinateActionManagerSDT::InitSettings(const TArray<FString>& Settings)
{
	return (Settings.Num() == 0);
}

const int8_t ACoordinateActionManagerSDT::PerformAction(TArray<FString>& ActionAndParameters)
{
	if (ActionAndParameters.Num() < 1)
	{
		UE_LOG(LogTemp, Error, TEXT("❌ No action specified"));
		return -1;
	}

	FString ActionName = ActionAndParameters[0];
	ActionAndParameters.RemoveAt(0);

	const int ActionID = ActionToID(ActionName);
	int8_t PerformActionCode = -1;

	switch (ActionID)
	{
	case MOVETO:
		PerformActionCode = MoveTo(ActionAndParameters);
		break;
	case GETPOS:
		PerformActionCode = GetPosition(ActionAndParameters);
		break;
	default:
		PerformActionCode = -1;
		UE_LOG(LogTemp, Error, TEXT("❌ Unknown action: %s"), *ActionName);
		break;
	}

	return PerformActionCode;
}

void ACoordinateActionManagerSDT::Possess()
{
	UE_LOG(LogTemp, Warning, TEXT("Setting View Target to: %s"), *GetActionManagerName());
	if (GetWorld())
	{
		APlayerController* PC = GetWorld()->GetFirstPlayerController();
		if (PC)
		{
			// CORREZIONE: Usiamo SetViewTarget invece di Possess
			// Questo dice al PlayerController di usare la camera di questo Actor
			PC->SetViewTarget(this);
		}
	}
}

void ACoordinateActionManagerSDT::UnPossess()
{
	if (GetWorld())
	{
		APlayerController* PC = GetWorld()->GetFirstPlayerController();
		if (PC)
		{
			// CORREZIONE: Rimettiamo la vista sul Pawn originale (se esiste) o resettiamo
			if (PC->GetPawn())
			{
				PC->SetViewTarget(PC->GetPawn());
			}
			else
			{
				// Fallback se non c'è un pawn
				PC->SetViewTarget(nullptr);
			}
		}
	}
}

FHitResult* ACoordinateActionManagerSDT::GetHitHandler()
{
	return ActorHit;
}

const int8_t ACoordinateActionManagerSDT::MoveTo(TArray<FString>& Parameters)
{
	if (Parameters.Num() != 7)
	{
		UE_LOG(LogTemp, Error, TEXT("ARGUMENT ERROR: 7 needed (x, y, z, qx, qy, qz, qw) but %i given"), Parameters.Num());
		return -1;
	}

	const float X = FCString::Atof(*Parameters[0]);
	const float Y = FCString::Atof(*Parameters[1]);
	const float Z = FCString::Atof(*Parameters[2]);
	const float QX = FCString::Atof(*Parameters[3]);
	const float QY = FCString::Atof(*Parameters[4]);
	const float QZ = FCString::Atof(*Parameters[5]);
	const float QW = FCString::Atof(*Parameters[6]);

	const FVector NewLocation = FVector(X, Y, Z);
	const FRotator NewRotation = FRotator(FQuat(QX, QY, QZ, QW));

	SetActorLocationAndRotation(NewLocation, NewRotation, false, ActorHit, ETeleportType::TeleportPhysics);

	return ActorHit->bBlockingHit ? 1 : 0;
}

const int8_t ACoordinateActionManagerSDT::GetPosition(TArray<FString>& Parameters)
{
	FVector Location = GetActorLocation();
	UE_LOG(LogTemp, Warning, TEXT("📍 Position: X=%.2f Y=%.2f Z=%.2f"), Location.X, Location.Y, Location.Z);
	return 0;
}

void ACoordinateActionManagerSDT::BeginPlay()
{
	Super::BeginPlay();
}

void ACoordinateActionManagerSDT::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}