package restoration

import (
	"time"

	"github.com/wowsims/sod/sim/core"
	"github.com/wowsims/sod/sim/core/proto"
	"github.com/wowsims/sod/sim/shaman"
)

func RegisterRestorationShaman() {
	core.RegisterAgentFactory(
		proto.Player_RestorationShaman{},
		proto.Spec_SpecRestorationShaman,
		func(character *core.Character, options *proto.Player) core.Agent {
			return NewRestorationShaman(character, options)
		},
		func(player *proto.Player, spec interface{}) {
			playerSpec, ok := spec.(*proto.Player_RestorationShaman)
			if !ok {
				panic("Invalid spec value for Restoration Shaman!")
			}
			player.Spec = playerSpec
		},
	)
}

func NewRestorationShaman(character *core.Character, options *proto.Player) *RestorationShaman {
	restoShamOptions := options.GetRestorationShaman()

	selfBuffs := shaman.SelfBuffs{
		Bloodlust: restoShamOptions.Options.Bloodlust,
		Shield:    restoShamOptions.Options.Shield,
	}

	if restoShamOptions.Rotation.Bloodlust != proto.RestorationShaman_Rotation_UnsetBloodlust {
		selfBuffs.Bloodlust = restoShamOptions.Rotation.Bloodlust == proto.RestorationShaman_Rotation_UseBloodlust
	}

	totems := &proto.ShamanTotems{}
	if restoShamOptions.Options.Totems != nil {
		totems = restoShamOptions.Options.Totems
	}

	resto := &RestorationShaman{
		Shaman:   shaman.NewShaman(character, options.TalentsString, totems, selfBuffs, false),
		rotation: restoShamOptions.Rotation,
	}

	// can only use earth shield if specc'd
	resto.rotation.UseEarthShield = resto.rotation.UseEarthShield && resto.Talents.EarthShield
	resto.earthShieldPPM = restoShamOptions.Options.EarthShieldPPM

	resto.EnableResumeAfterManaWait(resto.tryUseGCD)

	if resto.HasMHWeapon() {
		resto.ApplyEarthlivingImbueToItem(resto.GetMHWeapon())
	}
	if resto.HasOHWeapon() {
		resto.ApplyEarthlivingImbueToItem(resto.GetOHWeapon())
	}

	return resto
}

type RestorationShaman struct {
	*shaman.Shaman

	rotation            *proto.RestorationShaman_Rotation
	earthShieldPPM      int32
	lastEarthShieldProc time.Duration
}

func (resto *RestorationShaman) GetShaman() *shaman.Shaman {
	return resto.Shaman
}

func (resto *RestorationShaman) Reset(sim *core.Simulation) {
	resto.Shaman.Reset(sim)
	resto.lastEarthShieldProc = -core.NeverExpires
}
func (resto *RestorationShaman) GetMainTarget() *core.Unit {
	// TODO: make this just grab first player that isn't self.
	target := resto.Env.Raid.GetFirstTargetDummy()
	if target == nil {
		return &resto.Unit
	} else {
		return &target.Unit
	}
}

func (resto *RestorationShaman) Initialize() {
	resto.CurrentTarget = resto.GetMainTarget()

	// Has to be here because earthliving can cast hots and needs Env to be set to create the hots.
	procMask := core.ProcMaskUnknown
	if resto.HasMHWeapon() {
		procMask |= core.ProcMaskMeleeMH
	}
	if resto.HasOHWeapon() {
		procMask |= core.ProcMaskMeleeOH
	}
	resto.RegisterEarthlivingImbue(procMask)

	resto.Shaman.Initialize()
	resto.Shaman.RegisterHealingSpells()
}
