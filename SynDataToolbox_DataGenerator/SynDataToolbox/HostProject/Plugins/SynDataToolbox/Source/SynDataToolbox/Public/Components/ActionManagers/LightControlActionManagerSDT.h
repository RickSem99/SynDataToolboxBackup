#pragma once

#include "CoreMinimal.h"
#include "Components/ActionManagers/ActionManagerSDT.h"
#include "Components/SpotLightComponent.h"
// Includi l'header del Coordinate Manager per poter fare il cast
#include "Components/ActionManagers/CoordinateActionManagerSDT.h" 
#include "LightControlActionManagerSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API ALightControlActionManagerSDT : public AActor, public IActionManagerSDT
{
	GENERATED_BODY()

public:
	ALightControlActionManagerSDT();

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	// Funzione modificata per trovare la luce dentro il manager
	void FindTargetLight();

public:
	// ... (Resto delle funzioni dell'interfaccia IActionManagerSDT invariate) ...
	virtual const FString GetActionManagerName() const override;
	virtual const FString GetActionManagerSetup() const override;
	virtual const int ActionToID(const FString& Action) const override;
	virtual const bool InitSettings(const TArray<FString>& Settings) override;
	virtual const int8_t PerformAction(TArray<FString>& Action) override;
	virtual FHitResult* GetHitHandler() override;
	virtual void Possess() override;
	virtual void UnPossess() override;

private:
	// Helper functions
	const int8_t SetLightColor(TArray<FString>& Parameters);
	const int8_t SetLightIntensity(TArray<FString>& Parameters);
	const int8_t SetLightRadius(TArray<FString>& Parameters);
	// const int8_t SetLightDirection(TArray<FString>& Parameters); // <-- NON PIU' NECESSARIO SE SOLIDALE ALLA CAMERA
	const int8_t SetInnerConeAngle(TArray<FString>& Parameters);
	const int8_t SetOuterConeAngle(TArray<FString>& Parameters);
	const int8_t SetAllLightParameters(TArray<FString>& Parameters);

	static const int UNKNOWN = -1;
	static const int SETCOLOR = 0;
	static const int SETINTENSITY = 1;
	static const int SETRADIUS = 2;
	static const int SETDIRECTION = 3; // Manteniamolo per compatibilità ID, ma sarà vuoto o userà rotazione relativa
	static const int SETINNERCONE = 4;
	static const int SETOUTERCONE = 5;
	static const int SETALL = 6;

	FHitResult* ActorHit;

	// Puntatore diretto al componente luce
	USpotLightComponent* LightComponent;
};