#include "Components/LevelManager/ActorTarget.h"

AActorTarget::AActorTarget()
{
	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = false;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ActorTargetMesh"));
	SetRootComponent(Mesh);
	ConstructorHelpers::FObjectFinder<UStaticMesh> StaticMeshAsset(TEXT("/SynDataToolbox/SensorMesh"));
	Mesh->SetStaticMesh(StaticMeshAsset.Object);
	Mesh->SetRelativeScale3D(FVector(0.5f, 0.5f, 0.5f));

}

void AActorTarget::BeginPlay()
{
	Super::BeginPlay();
}

void AActorTarget::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
}
