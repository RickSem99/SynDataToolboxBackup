// ============================================================================
// ExclusionZoneSDT.cpp - VERSIONE CORRETTA E SICURA
// ============================================================================

#include "Components/ActionManagers/ExclusionZoneSDT.h"
#include "DrawDebugHelpers.h"

AExclusionZoneSDT::AExclusionZoneSDT()
{
    PrimaryActorTick.bCanEverTick = false;
    bIsInitialized = false;

    // Crea il Box Component
    ExclusionBox = CreateDefaultSubobject<UBoxComponent>(TEXT("ExclusionBox"));

    if (ExclusionBox)
    {
        SetRootComponent(ExclusionBox);

        // Configurazione visibilità
        ExclusionBox->SetVisibility(true);
        ExclusionBox->SetHiddenInGame(true);

        // Disabilita collisioni (solo volume visivo)
        ExclusionBox->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        ExclusionBox->SetCollisionResponseToAllChannels(ECR_Ignore);

        // Dimensioni default (100x100x100 cm)
        ExclusionBox->SetBoxExtent(FVector(50.0f, 50.0f, 50.0f));

        // Colore editor
        ExclusionBox->ShapeColor = FColor(255, 0, 0, 100);

        bIsInitialized = true;

        UE_LOG(LogTemp, Log, TEXT("✅ ExclusionZoneSDT: BoxComponent creato correttamente"));
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("❌ ExclusionZoneSDT: ERRORE durante creazione BoxComponent!"));
    }
}

void AExclusionZoneSDT::BeginPlay()
{
    Super::BeginPlay();

    // Verifica post-BeginPlay
    InitializeBoxComponent();

    if (IsZoneValid())
    {
        FVector Center = GetActorLocation();
        FVector Extent = ExclusionBox->GetScaledBoxExtent();
        FVector Size = Extent * 2.0f;

        UE_LOG(LogTemp, Warning, TEXT("🚫 ExclusionZone attiva:"));
        UE_LOG(LogTemp, Warning, TEXT("   Centro: (%.2f, %.2f, %.2f)"),
            Center.X, Center.Y, Center.Z);
        UE_LOG(LogTemp, Warning, TEXT("   Dimensioni: (%.2f, %.2f, %.2f)"),
            Size.X, Size.Y, Size.Z);

#if WITH_EDITOR
        if (GEngine && GetWorld())
        {
            DrawDebugBox(
                GetWorld(),
                Center,
                Extent,
                FColor::Red,
                true,   // persistente
                -1.0f,  // durata infinita
                0,
                5.0f    // spessore
            );
        }
#endif
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("❌ ExclusionZone NON VALIDA - Verrà ignorata!"));
    }
}

void AExclusionZoneSDT::InitializeBoxComponent()
{
    if (!ExclusionBox)
    {
        UE_LOG(LogTemp, Error, TEXT("❌ ExclusionZoneSDT: ExclusionBox è nullptr! Tentativo di recupero..."));

        ExclusionBox = FindComponentByClass<UBoxComponent>();

        if (ExclusionBox)
        {
            UE_LOG(LogTemp, Warning, TEXT("⚠️ ExclusionZoneSDT: BoxComponent recuperato tramite FindComponent"));
            bIsInitialized = true;
        }
        else
        {
            UE_LOG(LogTemp, Error, TEXT("❌ ExclusionZoneSDT: Impossibile recuperare BoxComponent!"));
            bIsInitialized = false;
            return;
        }
    }

    // Verifica correttezza del componente
    if (!::IsValid(ExclusionBox))
    {
        UE_LOG(LogTemp, Error, TEXT("❌ ExclusionBox non valido (pending kill)"));
        bIsInitialized = false;
        return;
    }

    bIsInitialized = true;
}

bool AExclusionZoneSDT::IsZoneValid() const
{
    return (ExclusionBox != nullptr &&
        ::IsValid(ExclusionBox) &&
        bIsInitialized);
}

FString AExclusionZoneSDT::GetZoneParameters() const
{
    if (!IsZoneValid())
    {
        UE_LOG(LogTemp, Error, TEXT("❌ GetZoneParameters chiamato su zona NON valida"));
        return FString();
    }

    const FVector Center = GetActorLocation();
    const FVector HalfExtent = ExclusionBox->GetScaledBoxExtent();

    const float SizeX = HalfExtent.X * 2.0f;
    const float SizeY = HalfExtent.Y * 2.0f;
    const float SizeZ = HalfExtent.Z * 2.0f;

    if (SizeX <= 0 || SizeY <= 0 || SizeZ <= 0)
    {
        UE_LOG(LogTemp, Error, TEXT("❌ ExclusionZone ha dimensioni invalide"));
        return FString();
    }

    FString Result = FString::Printf(TEXT("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f"),
        Center.X, Center.Y, Center.Z,
        SizeX, SizeY, SizeZ);

    UE_LOG(LogTemp, Verbose, TEXT("📦 GetZoneParameters: %s"), *Result);

    return Result;
}
