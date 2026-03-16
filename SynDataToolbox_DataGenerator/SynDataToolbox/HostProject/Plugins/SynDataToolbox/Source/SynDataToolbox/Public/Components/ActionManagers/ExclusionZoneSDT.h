// ============================================================================
// ExclusionZoneSDT.h - VERSIONE SICURA (senza override di IsValid())
// ============================================================================

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/BoxComponent.h"
#include "ExclusionZoneSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API AExclusionZoneSDT : public AActor
{
    GENERATED_BODY()

public:

    // Costruttore
    AExclusionZoneSDT();

    // Componente Box per definire la zona di esclusione
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Exclusion Zone")
    UBoxComponent* ExclusionBox;

    /**
     * Restituisce i parametri della zona (Centro e Dimensioni)
     * Formato: CenterX,CenterY,CenterZ,SizeX,SizeY,SizeZ
     * @return Stringa formattata con i parametri, stringa vuota se invalido
     */
    FString GetZoneParameters() const;

    /**
     * Verifica se la zona è valida e utilizzabile
     * @return true se la zona ha un BoxComponent valido
     */
    bool IsZoneValid() const;        // 🔥 SAFE NAME — evita conflitti con UObject::IsValid()

protected:

    // Chiamato a inizio gioco
    virtual void BeginPlay() override;

    // Flag per verificare se il componente è stato inizializzato correttamente
    bool bIsInitialized;

private:

    /**
     * Inizializza e valida il BoxComponent
     */
    void InitializeBoxComponent();
};
