#pragma once

#include "CoreMinimal.h"
#include "Components/ActionManagers/ActionManagerSDT.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/SpotLightComponent.h" 
#include "CoordinateActionManagerSDT.generated.h"

/**
 * Gestisce il movimento di camera e luce solidale.
 */
UCLASS()
class SYNDATATOOLBOX_API ACoordinateActionManagerSDT : public AActor, public IActionManagerSDT
{
	GENERATED_BODY()

public:
	ACoordinateActionManagerSDT();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	USpringArmComponent* CameraSpringArm;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	UCameraComponent* CameraComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Light")
	USpotLightComponent* SpotLightComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Mesh")
	UStaticMeshComponent* Mesh;

protected:
	virtual void BeginPlay() override;

public:
	virtual void Tick(float DeltaTime) override;

	// Interfaccia IActionManagerSDT
	virtual const FString GetActionManagerName() const override;
	virtual const FString GetActionManagerSetup() const override;
	virtual const bool IsActionManagerName(const FString& Name) const override { return Name == GetActionManagerName(); }
	virtual const int ActionToID(const FString& Action) const override;
	virtual const bool InitSettings(const TArray<FString>& Settings) override;
	virtual const int8_t PerformAction(TArray<FString>& Action) override;
	virtual FHitResult* GetHitHandler() override;

	virtual void Possess() override;
	virtual void UnPossess() override;

	virtual void ResetPhysics() override {}

private:
	static const int UNKNOWN = -1;
	static const int MOVETO = 0;
	static const int GETPOS = 1;

	const int8_t MoveTo(TArray<FString>& Parameters);
	const int8_t GetPosition(TArray<FString>& Parameters);

	FHitResult* ActorHit;
};